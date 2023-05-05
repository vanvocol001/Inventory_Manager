from typing import List

import hashlib
import uvicorn
import secrets
import permissions

from fastapi import Depends, FastAPI, HTTPException, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from pathlib import Path

from database import crud, models, schemas
from database.database import SessionLocal, engine

app = FastAPI()

templates = Jinja2Templates(directory='templates')

app.mount(
    '/static',
    StaticFiles(directory=Path(__file__).parent.absolute() / 'static'),
    name='static'
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def confirm_delivery(delivery_id: int, db: Session = Depends(get_db)) -> bool:
    delivery = crud.get_delivery(db, delivery_id)
    if delivery is not None:
        items = crud.get_items_from_delivery(db, delivery_id)
        for order, item in items:
            crud.add_to_stock(db, item.productID, order.quantityOrdered)
        return crud.set_delivery_confirmed(db, delivery_id)
    return False


def verify_permission(request: Request, perm_name: str, db: Session = Depends(get_db)) -> bool:
    user_id = get_user_from_cookie(request, db)
    user = crud.get_user(db, user_id)
    return permissions.verify_permission(perm_name, user.accountLevel)


def get_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    cookie = request.cookies.get("_SESSION")
    if cookie is not None:
        session = crud.get_user_session(db, cookie)
        if session is not None:
            return session.userID
    return None


def is_user_admin(userid: str, db: Session = Depends(get_db)):
    user = crud.get_user(db, userid)
    if user is not None:
        return user.accountLevel >= 10
    return False


@app.get("/error/", response_class=HTMLResponse)
def get_errorpage(request: Request):
    return templates.TemplateResponse("redirects/error.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
def get_mainpage(request: Request, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        return RedirectResponse("/homepage")
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def user_login(userid: str = Form(...), password: str = Form(...),
                     db: Session = Depends(get_db)):
    user = crud.get_user(db, userid=userid)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {userid} was not found.")
    else:
        hash_pw = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if user.password == hash_pw:
            crud.delete_old_user_sessions(db, user.userID)

            cookie_value = secrets.token_urlsafe(32)
            new_session = models.Session(cookie=cookie_value, userID=user.userID)
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            redirect_response = RedirectResponse(url="/homepage", status_code=302)
            redirect_response.set_cookie(key="_SESSION", value=cookie_value, expires=43200)
            return redirect_response
        else:
            return RedirectResponse(url="/homepage", status_code=302)


@app.get("/logout")
def user_logout(request: Request, db: Session = Depends(get_db)):
    cookie = request.cookies.get("_SESSION")
    redirect_response = RedirectResponse(url="/", status_code=302)
    if cookie is not None:
        redirect_response.delete_cookie("_SESSION")
    else:
        return {"status": "not logged in"}

    db_cookie = db.query(models.Session).where(models.Session.cookie == cookie).first()
    if db_cookie is not None:
        db.delete(db_cookie)
        db.commit()
        return redirect_response
    else:
        return {"status": "cookie not found in database"}


@app.get("/register/{result}")
def user_register_redirect(request: Request, result: bool):
    return templates.TemplateResponse("redirects/register.html", {"request": request, "result": result})


@app.post("/register")
def user_register(userid: str = Form(...), firstname: str = Form(...), lastname: str = Form(...),
                  password: str = Form(...), passwordconfirm: str = Form(...), db: Session = Depends(get_db)):
    if password != passwordconfirm:
        return RedirectResponse(url="/register/false", status_code=302)

    check_user = crud.get_user(db, userid=userid)
    if check_user is not None:
        return RedirectResponse(url="/register/false", status_code=302)
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    new_user = models.User(userID=userid, firstName=firstname, lastName=lastname, accountLevel=0,
                           password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RedirectResponse(url="/register/true", status_code=302)


@app.post("/add_product")
def add_product_endpoint(request: Request, product_description: str = Form(...), supplier_id: int = Form(...),
                         stock: int = Form(...), restock_limit: int = Form(...), db: Session = Depends(get_db)):
    if not verify_permission(request, "ProductCreate", db):
        return RedirectResponse(url="/error/", status_code=302)

    verify_supplier = crud.get_supplier(db, supplier_id)
    if verify_supplier is not None:
        crud.add_inventory_item(db, product_description, supplier_id, stock, restock_limit)
        redirect_response = RedirectResponse(url="/products", status_code=302)
        return redirect_response
    return RedirectResponse(url="/homepage", status_code=302)


@app.post("/add_delivery")
async def add_delivery_endpoint(request: Request, date: str = Form(...), supplier_id: int = Form(...),
                                product: List[int] = Form(...), stock: List[int] = Form(...),
                                db: Session = Depends(get_db)):
    if not verify_permission(request, "DeliveryCreate", db):
        return RedirectResponse(url="/error/", status_code=302)

    crud.add_delivery(db, date, supplier_id, product, stock)
    return RedirectResponse("/deliveries", status_code=302)


@app.post("/add_transaction")
async def add_transaction_endpoint(request: Request, product: List[int] = Form(...), stock: List[int] = Form(...),
                                   db: Session = Depends(get_db)):
    if not verify_permission(request, "TransactionCreate", db):
        return RedirectResponse(url="/error/", status_code=302)

    crud.add_transaction(db, product, stock)
    for product_id, quantity in zip(product, stock):
        crud.subtract_from_stock(db, product_id, quantity)
    return RedirectResponse("/transactions", status_code=302)


@app.post("/add_disposal")
async def add_disposal_endpoint(request: Request, reason: str = Form(...), product: List[int] = Form(...),
                                stock: List[int] = Form(...), db: Session = Depends(get_db)):
    if not verify_permission(request, "DisposalCreate", db):
        return RedirectResponse(url="/error/", status_code=302)

    user = get_user_from_cookie(request, db)
    crud.add_disposal(db, user, reason, product, stock)
    for product_id, quantity in zip(product, stock):
        crud.subtract_from_stock(db, product_id, quantity)
    return RedirectResponse("/disposals", status_code=302)


@app.post("/add_supplier")
def add_supplier_endpoint(request: Request, name: str = Form(...), address: str = Form(...),
                          db: Session = Depends(get_db)):
    if not verify_permission(request, "SupplierCreate", db):
        return RedirectResponse(url="/error/", status_code=302)

    crud.add_supplier(db, name, address)
    return RedirectResponse("/suppliers", status_code=302)


@app.post("/user_changes")
async def save_user_changes(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    for header in form_data:
        account_level = form_data[header]
        if account_level != '':
            user_id = header[14:]
            crud.update_account_level(db, user_id, int(account_level))
    return RedirectResponse("/users", status_code=302)


@app.get("/delete_user/{user_id}")
def delete_user(request: Request, user_id: str, db: Session = Depends(get_db)):
    current_user = get_user_from_cookie(request, db)
    if is_user_admin(current_user, db) and not is_user_admin(user_id, db):
        if current_user != user_id:
            crud.delete_user(db, user_id)
    return RedirectResponse("/users", status_code=302)


@app.post("/permission_changes")
async def save_permission_changes(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()

    new_perms = {}
    for header in form_data:
        if form_data[header] != "":
            new_perms[header] = form_data[header]
    permissions.update_config(new_perms)
    return RedirectResponse("/permissions", status_code=302)


@app.get("/confirm_delivery")
async def confirm_delivery_endpoint(request: Request, delivery_id: int, db: Session = Depends(get_db)):
    if not verify_permission(request, "DeliveryConfirm", db):
        return RedirectResponse(url="/error/", status_code=302)

    confirm_delivery(delivery_id, db)
    return RedirectResponse("/deliveries", status_code=302)


@app.post("/reject_delivery")
async def reject_delivery_endpoint(request: Request, delivery_id: int = Form(...), reason: str = Form(...),
                                   db: Session = Depends(get_db)):
    if not verify_permission(request, "DeliveryReject", db):
        return RedirectResponse(url="/error/", status_code=302)

    crud.set_delivery_rejected(db, delivery_id, reason)
    return RedirectResponse("/deliveries", status_code=302)


@app.get("/homepage/", response_class=HTMLResponse)
def get_homepage(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        inventory_items = crud.get_inventory_items(db, skip=skip, limit=limit)
        deliveries = crud.get_deliveries(db, skip=skip, limit=limit)
        deliveries.reverse()
        disposals = crud.get_disposals(db, skip=skip, limit=limit)
        disposals.reverse()
        is_admin = is_user_admin(user, db)
        return templates.TemplateResponse("overview.html", {"request": request, "products": inventory_items,
                                                            "deliveries": deliveries, "disposals": disposals,
                                                            "user": user, "is_admin": is_admin})
    return RedirectResponse("/error")


@app.get("/products/", response_class=HTMLResponse)
def read_inventory_items(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        inventory_items = crud.get_inventory_items(db, skip=skip, limit=limit)
        suppliers = crud.get_suppliers(db, skip=skip, limit=limit)
        is_admin = is_user_admin(user, db)
        perms = {
            "ProductCreate": verify_permission(request, "ProductCreate", db)
        }
        return templates.TemplateResponse("products.html", {"request": request, "products": inventory_items,
                                                            "suppliers": suppliers, "user": user, "is_admin": is_admin,
                                                            "perms": perms})
    return RedirectResponse("/error")


@app.get("/deliveries/", response_class=HTMLResponse)
def read_deliveries(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        deliveries = crud.get_deliveries(db, skip=skip, limit=limit)
        products = crud.get_inventory_items(db, skip=skip, limit=limit)
        suppliers = crud.get_suppliers(db, skip=skip, limit=limit)
        is_admin = is_user_admin(user, db)
        perms = {
            "DeliveryCreate": verify_permission(request, "DeliveryCreate", db),
            "DeliveryConfirm": verify_permission(request, "DeliveryConfirm", db),
            "DeliveryReject": verify_permission(request, "DeliveryReject", db)
        }
        return templates.TemplateResponse("deliveries.html", {"request": request, "deliveries": deliveries,
                                                              "products": products, "suppliers": suppliers,
                                                              "user": user, "is_admin": is_admin, "perms": perms})
    return RedirectResponse("/error")


@app.get("/disposals/", response_class=HTMLResponse)
def read_disposals(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        disposals = crud.get_disposals(db, skip=skip, limit=limit)
        products = crud.get_inventory_items(db, skip=skip, limit=limit)
        is_admin = is_user_admin(user, db)
        perms = {
            "DisposalCreate": verify_permission(request, "DisposalCreate", db)
        }
        return templates.TemplateResponse("disposals.html", {"request": request, "disposals": disposals,
                                                             "products": products, "user": user, "is_admin": is_admin,
                                                             "perms": perms})
    return RedirectResponse("/error")


@app.get("/transactions/", response_class=HTMLResponse)
def read_transactions(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        transactions = crud.get_transactions(db, skip=skip, limit=limit)
        products = crud.get_inventory_items(db, skip=skip, limit=limit)
        is_admin = is_user_admin(user, db)
        perms = {
            "TransactionCreate": verify_permission(request, "TransactionCreate", db)
        }
        return templates.TemplateResponse("transactions.html", {"request": request, "transactions": transactions,
                                                                "products": products, "user": user,
                                                                "is_admin": is_admin, "perms": perms})
    return RedirectResponse("/error")


@app.get("/suppliers/", response_class=HTMLResponse)
def read_suppliers(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        suppliers = crud.get_suppliers(db, skip=skip, limit=limit)
        is_admin = is_user_admin(user, db)
        perms = {
            "SupplierCreate": verify_permission(request, "SupplierCreate", db)
        }
        return templates.TemplateResponse("suppliers.html", {"request": request, "suppliers": suppliers,
                                                             "user": user, "is_admin": is_admin, "perms": perms})
    return RedirectResponse("/error")


@app.get("/users/", response_class=HTMLResponse)
def read_users(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        is_admin = is_user_admin(user, db)
        if is_admin:
            users = crud.get_users(db, skip=skip, limit=limit)
            return templates.TemplateResponse("users.html", {"request": request, "users": users,
                                                             "user": user, "is_admin": is_admin})
    return RedirectResponse("/error")


@app.get("/permissions/", response_class=HTMLResponse)
def read_permissions(request: Request, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        is_admin = is_user_admin(user, db)
        if is_admin:
            perms = permissions.get_permissions()
            return templates.TemplateResponse("permissions.html", {"request": request, "user": user,
                                                                   "is_admin": is_admin, "perms": perms})
    return RedirectResponse("/error")


if __name__ == "__main__":
    uvicorn.run(app)
