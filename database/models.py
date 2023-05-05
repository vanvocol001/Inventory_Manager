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
    supplierID = Column(Integer, ForeignKey("supplier.supplierID"))
    stock = Column(Integer)
    restockLimit = Column(Integer)
    image = Column(String)

    supplier = relationship("Supplier")


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

    product = relationship("InventoryItem")


class Transaction(Base):
    __tablename__ = "transaction"

    transactionID = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=func.current_date())

    transactions = relationship("TransactionReport")


class InventoryOrder(Base):
    __tablename__ = "inventoryorder"

    deliveryID = Column(Integer, ForeignKey("delivery.deliveryID"), primary_key=True, index=True)
    productID = Column(Integer, ForeignKey("inventoryitem.productID"), primary_key=True, index=True)
    quantityOrdered = Column(Integer)

    product = relationship("InventoryItem")


class Delivery(Base):
    __tablename__ = "delivery"

    deliveryID = Column(Integer, primary_key=True, index=True)
    dateOrdered = Column(Date, default=func.current_date())
    dateExpected = Column(Date)
    supplierID = Column(Integer, ForeignKey("supplier.supplierID"))
    status = Column(String, default="pending")
    reason = Column(String)

    items = relationship("InventoryOrder")


class DisposedInventoryReport(Base):
    __tablename__ = "disposedinventoryreport"

    disposalID = Column(Integer, ForeignKey("disposedinventory.disposalID"), primary_key=True)
    productID = Column(Integer, ForeignKey("inventoryitem.productID"), primary_key=True)
    quantityDisposed = Column(Integer)

    product = relationship("InventoryItem")


class DisposedInventory(Base):
    __tablename__ = "disposedinventory"

    disposalID = Column(Integer, primary_key=True, index=True)
    dateDisposed = Column(Date, default=func.current_date())
    reason = Column(String)
    userID = Column(String, ForeignKey("user.userID"))

    items = relationship("DisposedInventoryReport")


class Permissions(Base):
    __tablename__ = "permissions"

    productCreate = Column(Integer, primary_key=True)
    deliveryCreate = Column(Integer)
    deliveryConfirm = Column(Integer)
    deliveryReject = Column(Integer)
    disposalCreate = Column(Integer)
    transactionCreate = Column(Integer)
    supplierCreate = Column(Integer)


class Session(Base):
    __tablename__ = "session"

    cookie = Column(String, primary_key=True)
    userID = Column(String, ForeignKey("user.userID"))

