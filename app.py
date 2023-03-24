from typing import List
import uvicorn

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from pathlib import Path

from pydantic import BaseModel, Field
from uuid import UUID

from database import crud, models, schemas
from database.database import SessionLocal, engine

#from app.model import PostSchema, UserSchema, UserLoginSchema
#from app.auth.auth_handler import signJWT

app = FastAPI()

templates = Jinja2Templates(directory='templates')

app.mount(
    '/static',
    StaticFiles(directory=Path(__file__).parent.absolute()/'static'),
    name='static'
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/products/{productid}", response_class=HTMLResponse)
def read_inventory_item(request: Request, productid: int, db: Session = Depends(get_db)):
    product = crud.get_inventory_item(db, productid=productid)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse("Homepage.html", {"request": request, "products": [product]})


@app.get("/products/", response_class=HTMLResponse)
def read_inventory_items(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    inventory_items = crud.get_inventory_items(db, skip=skip, limit=limit)
    return templates.TemplateResponse("Homepage.html", {"request": request, "products": inventory_items})


@app.get("/suppliers/{supplierid}", response_model=schemas.Supplier)
def read_supplier(supplierid: int, db: Session = Depends(get_db)):
    supplier = crud.get_supplier(db, supplierid=supplierid)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@app.get("/suppliers/", response_model=List[schemas.Supplier])
def read_suppliers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    suppliers = crud.get_suppliers(db, skip=skip, limit=limit)
    return suppliers


@app.get("/users/{userid}", response_model=schemas.User)
def read_user(userid: str, db: Session = Depends(get_db)):
    user = crud.get_user(db, userid=userid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/transactions/{transactionid}", response_model=schemas.Transaction)
def read_transaction(transactionid: int, db: Session = Depends(get_db)):
    transaction = crud.get_transaction(db, transactionid=transactionid)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@app.get("/transactions/", response_model=List[schemas.Transaction])
def read_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transactions = crud.get_transactions(db, skip=skip, limit=limit)
    return transactions


@app.get("/deliveries/{deliveryid}", response_model=schemas.Delivery)
def read_delivery(deliveryid: int, db: Session = Depends(get_db)):
    delivery = crud.get_delivery(db, deliveryid=deliveryid)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery


@app.get("/deliveries/", response_model=List[schemas.Delivery])
def read_deliveries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    deliveries = crud.get_deliveries(db, skip=skip, limit=limit)
    return deliveries


@app.get("/disposals/{disposalid}", response_model=schemas.DisposedInventory)
def read_disposal(disposalid: int, db: Session = Depends(get_db)):
    disposal = crud.get_disposal(db, disposalid=disposalid)
    if disposal is None:
        raise HTTPException(status_code=404, detail="Disposal not found")
    return disposal


@app.get("/disposals/", response_model=List[schemas.DisposedInventory])
def read_disposals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    disposals = crud.get_disposals(db, skip=skip, limit=limit)
    return disposals


if __name__ == "__main__":
    uvicorn.run(app)
