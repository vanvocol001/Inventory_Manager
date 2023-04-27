from typing import List

import hashlib
import uvicorn
import secrets

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
def user_logout(request: Request, response: Response, db: Session = Depends(get_db)):
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


@app.post("/register")
def user_register(userid: str = Form(...), firstname: str = Form(...), lastname: str = Form(...),
                  password: str = Form(...), db: Session = Depends(get_db)):
    check_user = crud.get_user(db, userid=userid)
    if check_user is not None:
        raise HTTPException(status_code=303, detail=f"User {userid} already exists")
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    new_user = models.User(userID=userid, firstName=firstname, lastName=lastname, accountLevel=0,
                           password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    redirect_response = RedirectResponse(url="/homepage", status_code=302)
    return redirect_response


@app.post("/add_product")
def add_product_endpoint(product_description: str = Form(...), supplier_id: int = Form(...), stock: int = Form(...),
                         restock_limit: int = Form(...), db: Session = Depends(get_db)):
    verify_supplier = crud.get_supplier(db, supplier_id)
    if verify_supplier is not None:
        crud.add_inventory_item(db, product_description, supplier_id, stock, restock_limit)
        redirect_response = RedirectResponse(url="/products", status_code=302)
        return redirect_response
    return RedirectResponse(url="/homepage", status_code=302)


@app.post("/add_delivery")
async def add_delivery_endpoint(date: str = Form(...), supplier_id: int = Form(...), product: List[int] = Form(...),
                                stock: List[int] = Form(...), db: Session = Depends(get_db)):
    crud.add_delivery(db, date, supplier_id, product, stock)
    return RedirectResponse("/deliveries", status_code=302)


@app.post("/add_transaction")
async def add_transaction_endpoint(product: List[int] = Form(...), stock: List[int] = Form(...),
                                   db: Session = Depends(get_db)):
    crud.add_transaction(db, product, stock)
    for product_id, quantity in zip(product, stock):
        crud.subtract_from_stock(db, product_id, quantity)
    return RedirectResponse("/transactions", status_code=302)


@app.post("/add_disposal")
async def add_disposal_endpoint(request: Request, reason: str = Form(...), product: List[int] = Form(...),
                                stock: List[int] = Form(...), db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    crud.add_disposal(db, user, reason, product, stock)
    for product_id, quantity in zip(product, stock):
        crud.subtract_from_stock(db, product_id, quantity)
    return RedirectResponse("/disposals", status_code=302)


@app.post("/add_supplier")
def add_supplier_endpoint(name: str = Form(...), address: str = Form(...), db: Session = Depends(get_db)):
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


@app.get("/confirm_delivery")
async def confirm_delivery_endpoint(delivery_id: int, db: Session = Depends(get_db)):
    confirm_delivery(delivery_id, db)
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
    return RedirectResponse(url="/")


@app.get("/products/{productid}", response_class=HTMLResponse)
def read_inventory_item(request: Request, productid: int, db: Session = Depends(get_db)):
    product = crud.get_inventory_item(db, productid=productid)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse("products.html", {"request": request, "products": [product]})


@app.get("/products/", response_class=HTMLResponse)
def read_inventory_items(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        inventory_items = crud.get_inventory_items(db, skip=skip, limit=limit)
        suppliers = crud.get_suppliers(db, skip=skip, limit=limit)
        is_admin = is_user_admin(user, db)
        return templates.TemplateResponse("products.html", {"request": request, "products": inventory_items,
                                                            "suppliers": suppliers, "user": user, "is_admin": is_admin})
    return RedirectResponse(url="/")


@app.get("/deliveries/{deliveryID}", response_class=HTMLResponse)
def read_delivery(request: Request, deliveryid: int, db: Session = Depends(get_db)):
    delivery = crud.get_delivery(db, deliveryid=deliveryid)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return templates.TemplateResponse("deliveries.html", {"request": request, "deliveries": [delivery]})


@app.get("/deliveries/", response_class=HTMLResponse)
def read_deliveries(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        deliveries = crud.get_deliveries(db, skip=skip, limit=limit)
        products = crud.get_inventory_items(db, skip=skip, limit=limit)
        suppliers = crud.get_suppliers(db, skip=skip, limit=limit)
        is_admin = is_user_admin(user, db)
        return templates.TemplateResponse("deliveries.html", {"request": request, "deliveries": deliveries,
                                                              "products": products, "suppliers": suppliers,
                                                              "user": user, "is_admin": is_admin})
    return RedirectResponse(url="/")


@app.get("/disposals/{disposalID}", response_class=HTMLResponse)
def read_disposal(request: Request, disposalid: int, db: Session = Depends(get_db)):
    disposal = crud.get_disposal(db, disposalid=disposalid)
    if disposal is None:
        raise HTTPException(status_code=404, detail="Disposal not found")
    return templates.TemplateResponse("disposals.html", {"request": request, "disposal": [disposal]})


@app.get("/disposals/", response_class=HTMLResponse)
def read_disposals(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        disposals = crud.get_disposals(db, skip=skip, limit=limit)
        products = crud.get_inventory_items(db, skip=skip, limit=limit)
        is_admin = is_user_admin(user, db)
        return templates.TemplateResponse("disposals.html", {"request": request, "disposals": disposals,
                                                             "products": products, "user": user, "is_admin": is_admin})
    return RedirectResponse(url="/")


@app.get("/transactions/{transactionID}", response_class=HTMLResponse)
def read_transaction(request: Request, transactionid: int, db: Session = Depends(get_db)):
    transaction = crud.get_transaction(db, transactionid=transactionid)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return templates.TemplateResponse("transactions.html", {"request": request, "transaction": [transaction]})


@app.get("/transactions/", response_class=HTMLResponse)
def read_transactions(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        transactions = crud.get_transactions(db, skip=skip, limit=limit)
        products = crud.get_inventory_items(db, skip=skip, limit=limit)
        is_admin = is_user_admin(user, db)
        return templates.TemplateResponse("transactions.html", {"request": request, "transactions": transactions,
                                                                "products": products, "user": user,
                                                                "is_admin": is_admin})
    return RedirectResponse(url="/")


@app.get("/suppliers/{supplierID}", response_class=HTMLResponse)
def read_supplier(request: Request, supplierid: int, db: Session = Depends(get_db)):
    supplier = crud.get_supplier(db, supplierid=supplierid)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return templates.TemplateResponse("suppliers.html", {"request": request, "supplier": [supplier]})


@app.get("/suppliers/", response_class=HTMLResponse)
def read_suppliers(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        suppliers = crud.get_suppliers(db, skip=skip, limit=limit)
        is_admin = is_user_admin(user, db)
        return templates.TemplateResponse("suppliers.html", {"request": request, "suppliers": suppliers,
                                                             "user": user, "is_admin": is_admin})
    return RedirectResponse(url="/")


@app.get("/users/{userid}", response_model=schemas.User)
def read_user(userid: str, db: Session = Depends(get_db)):
    user = crud.get_user(db, userid=userid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/", response_class=HTMLResponse)
def read_users(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        is_admin = is_user_admin(user, db)
        if is_admin:
            users = crud.get_users(db, skip=skip, limit=limit)
            return templates.TemplateResponse("users.html", {"request": request, "users": users,
                                                             "user": user, "is_admin": is_admin})
    return RedirectResponse("/")


if __name__ == "__main__":
    uvicorn.run(app)
