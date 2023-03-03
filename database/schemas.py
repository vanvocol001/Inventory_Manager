from typing import List, Union

from pydantic import BaseModel
from datetime import date


class User(BaseModel):
    userID: str
    firstName: str
    lastName: str
    accountLevel: int

    class Config:
        orm_mode = True


class InventoryItem(BaseModel):
    productID: int
    description: str
    supplierID: int
    stock: int
    restockLimit: int
    image: Union[str, None] = None

    class Config:
        orm_mode = True


class Supplier(BaseModel):
    supplierID: int
    name: str
    address: str

    class Config:
        orm_mode = True


class TransactionReport(BaseModel):
    productID: int
    quantitySold: int

    class Config:
        orm_mode = True


class Transaction(BaseModel):
    transactionID: int
    date: date

    transactions: list[TransactionReport] = []

    class Config:
        orm_mode = True
