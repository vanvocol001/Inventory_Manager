from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.database import Base


class User(Base):
    __tablename__ = "user"

    userID = Column(String, primary_key=True, index=True)
    firstName = Column(String, index=True)
    lastName = Column(String, index=True)
    accountLevel = Column(Integer)
    password = Column(String)


class InventoryItem(Base):
    __tablename__ = "inventoryitem"

    productID = Column(Integer, primary_key=True)
    description = Column(String)
    supplierID = Column(Integer, ForeignKey("Supplier.supplierID"))
    stock = Column(Integer)
    restockLimit = Column(Integer)
    image = Column(String)


class Supplier(Base):
    __tablename__ = "supplier"

    supplierID = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    address = Column(String)


class TransactionReport(Base):
    __tablename__ = "transactionreport"

    transactionID = Column(Integer, ForeignKey("transaction.transactionID"), primary_key=True)
    productID = Column(Integer, ForeignKey("inventoryitem.productID"), primary_key=True)
    quantitySold = Column(Integer)


class Transaction(Base):
    __tablename__ = "transaction"

    transactionID = Column(Integer, primary_key=True, index=True)
    date = Column(Date, server_default=func.now())

    transactions = relationship("TransactionReport")


class InventoryOrder(Base):
    __tablename__ = "inventoryorder"

    deliveryID = Column(Integer, ForeignKey("delivery.deliveryID"), primary_key=True, index=True)
    productID = Column(Integer, ForeignKey("inventoryitem.productID"), primary_key=True, index=True)
    quantityOrdered = Column(Integer)


class Delivery(Base):
    __tablename__ = "delivery"

    deliveryID = Column(Integer, primary_key=True, index=True)
    dateOrdered = Column(Date, server_default=func.now())
    dateExpected = Column(Date)
    supplierID = Column(Integer, ForeignKey("supplier.supplierID"))

    items = relationship("InventoryOrder")


class DisposedInventoryReport(Base):
    __tablename__ = "disposedinventoryreport"

    disposalID = Column(Integer, ForeignKey("disposedinventory.disposalID"), primary_key=True)
    productID = Column(Integer, ForeignKey("inventoryitem.productID"), primary_key=True)
    quantityDisposed = Column(Integer)


class DisposedInventory(Base):
    __tablename__ = "disposedinventory"

    disposalID = Column(Integer, primary_key=True, index=True)
    dateDisposed = Column(Date, server_default=func.now())
    reason = Column(String)
    userID = Column(String, ForeignKey("user.userID"))

    disposalReport = relationship("DisposedInventoryReport")


class Session(Base):
    __tablename__ = "session"

    cookie = Column(String, primary_key=True)
    userID = Column(String, ForeignKey("user.userID"))

