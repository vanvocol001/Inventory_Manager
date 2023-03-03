from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "User"

    userID = Column(String, primary_key=True, index=True)
    firstName = Column(String, index=True)
    lastName = Column(String, index=True)
    accountLevel = Column(Integer)
    password = Column(String)


class InventoryItem(Base):
    __tablename__ = "InventoryItem"

    productID = Column(Integer, primary_key=True)
    description = Column(String)
    supplierID = Column(Integer, ForeignKey("Supplier.supplierID"))
    stock = Column(Integer)
    restockLimit = Column(Integer)
    image = Column(String)


class Supplier(Base):
    __tablename__ = "Supplier"

    supplierID = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    address = Column(String)