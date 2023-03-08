from sqlalchemy.orm import Session

from . import models


def get_inventory_item(db: Session, productid: int):
    return db.query(models.InventoryItem).filter(models.InventoryItem.productID == productid).first()


def get_inventory_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.InventoryItem).offset(skip).limit(limit).all()


def get_supplier(db: Session, supplierid: int):
    return db.query(models.Supplier).filter(models.Supplier.supplierID == supplierid).first()


def get_suppliers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Supplier).offset(skip).limit(limit).all()


def get_user(db: Session, userid: str):
    return db.query(models.User).filter(models.User.userID == userid).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def get_transaction(db: Session, transactionid: int):
    return db.query(models.Transaction).filter(models.Transaction.transactionID == transactionid).first()


def get_transactions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).offset(skip).limit(limit).all()


def get_delivery(db: Session, deliveryid: int):
    return db.query(models.Delivery).filter(models.Delivery.deliveryID == deliveryid).first()


def get_deliveries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Delivery).offset(skip).limit(limit).all()


def get_disposal(db: Session, disposalid: int):
    return db.query(models.DisposedInventory).filter(models.DisposedInventory.disposalID == disposalid).first()


def get_disposals(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DisposedInventory).offset(skip).limit(limit).all()
