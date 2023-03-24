from typing import List, Union, Any

import pydantic.utils
from pydantic import BaseModel, Field, EmailStr
from datetime import date


class ORMModel(BaseModel):
    class Config:
        orm_mode = True


class User(ORMModel):
    userID: str
    firstName: str
    lastName: str
    accountLevel: int
    password: str
    
class UserLogin(ORMModel):
    userID: str
    password: str


class InventoryItem(ORMModel):
    productID: int
    description: str
    supplierID: int
    stock: int
    restockLimit: int
    image: Union[str, None] = None


class Supplier(ORMModel):
    supplierID: int
    name: str
    address: str


class TransactionReport(ORMModel):
    productID: int
    quantitySold: int


class Transaction(ORMModel):
    transactionID: int
    date: date

    transactions: list[TransactionReport] = []


class InventoryOrder(ORMModel):
    deliveryID: int
    productID: int
    quantityOrdered: int


class Delivery(ORMModel):
    deliveryID: int
    dateOrdered: date
    dateExpected: date
    supplierID: int

    items: list[InventoryOrder] = []


class DisposedInventoryReport(ORMModel):
    disposalID: int
    productID: int
    quantityDisposed: int


class DisposedInventory(ORMModel):
    disposalID: int
    dateDisposed: date
    reason: str
    userID: str

    disposalReport: list[DisposedInventoryReport] = []
