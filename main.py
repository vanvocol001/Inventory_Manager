from typing import List
from collections import defaultdict

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


def collate_deliveries(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    deliveries_dict = {}
    deliveries = crud.get_deliveries(db, skip=skip, limit=limit)

    for delivery in deliveries:
        # Setup default dict for new delivery IDs
        if delivery.deliveryID not in deliveries_dict:
            deliveries_dict[delivery.deliveryID] = {
                "deliveryID": delivery.deliveryID,
                "dateExpected": delivery.dateExpected,
                "dateOrdered": delivery.dateOrdered,
                "itemsOrdered": {},
            }

        currentDelivery = deliveries_dict[delivery.deliveryID]
        itemsOrdered = crud.get_items_from_delivery(db, delivery.deliveryID)
        for item in itemsOrdered:
            # GET ACTUAL PRODUCT NAMES LATER, NOT PRODUCT IDS.
            # Join Deliveries on InventoryItems with ProductID as the key
            currentDelivery["itemsOrdered"][item.productID] = item.quantityOrdered
    return deliveries_dict


def collate_disposals(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    disposals_dict = {}
    disposals = crud.get_disposals(db, skip=skip, limit=limit)

    for disposal in disposals:
        # Setup default dict for new disposal IDs
        if disposal.disposalID not in disposals_dict:
            disposals_dict[disposal.disposalID] = {
                "disposalID": disposal.disposalID,
                "dateDisposed": disposal.dateDisposed,
                "reason": disposal.reason,
                "user": disposal.userID,
                "itemsDisposed": {},
            }

        current_disposal = disposals_dict[disposal.disposalID]
        items_disposed = crud.get_items_from_disposal(db, disposal.disposalID)
        for item in items_disposed:
            current_disposal["itemsDisposed"][item.productID] = item.quantityDisposed
    return disposals_dict


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
            cookie_value = secrets.token_urlsafe(32)
            new_session = models.Session(cookie=cookie_value, userID=userid)
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            redirect_response = RedirectResponse(url="/homepage", status_code=302)
            redirect_response.set_cookie(key="_SESSION", value=cookie_value, expires=43200)
            return redirect_response
        else:
            return "failure"


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


@app.get("/homepage/", response_class=HTMLResponse)
def get_homepage(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user = get_user_from_cookie(request, db)
    if user is not None:
        inventory_items = crud.get_inventory_items(db, skip=skip, limit=limit)
        deliveries = collate_deliveries(db, skip=skip, limit=limit)
        disposals = collate_disposals(db, skip=skip, limit=limit)
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
        is_admin = is_user_admin(user, db)
        return templates.TemplateResponse("products.html", {"request": request, "products": inventory_items,
                                                            "user": user, "is_admin": is_admin})
    else:
        return {"error": "You must be logged in."}


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
        deliveries = collate_deliveries(db, skip=skip, limit=limit)
        is_admin = is_user_admin(user, db)
        return templates.TemplateResponse("deliveries.html", {"request": request, "deliveries": deliveries,
                                                              "user": user, "is_admin": is_admin})
    else:
        return {"error": "You must be logged in."}


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
        is_admin = is_user_admin(user, db)
        return templates.TemplateResponse("disposals.html", {"request": request, "disposals": disposals,
                                                             "user": user, "is_admin": is_admin})
    else:
        return {"error": "You must be logged in."}


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
        is_admin = is_user_admin(user, db)
        return templates.TemplateResponse("transactions.html", {"request": request, "transactions": transactions,
                                                                "user": user, "is_admin": is_admin})
    else:
        return {"error": "You must be logged in."}


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
    else:
        return {"error": "You must be logged in."}


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
