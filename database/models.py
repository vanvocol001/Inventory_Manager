from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.database import Base


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


class TransactionReport(Base):
    __tablename__ = "TransactionReport"

    transactionID = Column(Integer, ForeignKey("Transaction.transactionID"), primary_key=True)
    productID = Column(Integer, ForeignKey("InventoryItem.productID"), primary_key=True)
    quantitySold = Column(Integer)

    transaction = relationship("Transaction", back_populates="transactions")


class Transaction(Base):
    __tablename__ = "Transaction"

    transactionID = Column(Integer, primary_key=True, index=True)
    date = Column(Date, server_default=func.now())

    transactions = relationship("TransactionReport", back_populates="transaction")


class InventoryOrder(Base):
    __tablename__ = "InventoryOrder"

    deliveryID = Column(Integer, ForeignKey("Delivery.deliveryID"), primary_key=True, index=True)
    productID = Column(Integer, ForeignKey("InventoryItem.productID"), primary_key=True, index=True)
    quantityOrdered = Column(Integer)


class Delivery(Base):
    __tablename__ = "Delivery"

    deliveryID = Column(Integer, primary_key=True, index=True)
    dateOrdered = Column(Date, server_default=func.now())
    dateExpected = Column(Date)
    supplierID = Column(Integer, ForeignKey("Supplier.SupplierID"))

    items = relationship("InventoryOrder")


class DisposedInventoryReport(Base):
    __tablename__ = "DisposedInventoryReport"

    disposalID = Column(Integer, ForeignKey("DisposedInventory.disposalID"), primary_key=True)
    productID = Column(Integer, ForeignKey("InventoryItem.productID"), primary_key=True)
    quantityDisposed = Column(Integer)


class DisposedInventory(Base):
    __tablename__ = "DisposedInventory"

    disposalID = Column(Integer, primary_key=True, index=True)
    dateDisposed = Column(Date, server_default=func.now())
    reason = Column(String)
    userID = Column(String, ForeignKey("User.userID"))

    disposalReport = relationship("DisposedInventoryReport")


class Session(Base):
    __tablename__ = "Session"

    cookie = Column(String, primary_key=True)
    userID = Column(String, ForeignKey("User.userID"))

