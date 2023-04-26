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


def get_items_from_delivery(db: Session, deliveryid: int):
    return db.query(models.InventoryOrder, models.InventoryItem).join(models.InventoryItem).filter(models.InventoryOrder.deliveryID == deliveryid).all()


def get_items_from_disposal(db: Session, disposalid: int):
    return db.query(models.DisposedInventoryReport, models.InventoryItem).join(models.InventoryItem).filter(models.DisposedInventoryReport.disposalID == disposalid).all()


def get_disposal(db: Session, disposalid: int):
    return db.query(models.DisposedInventory).filter(models.DisposedInventory.disposalID == disposalid).first()


def get_disposals(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DisposedInventory).offset(skip).limit(limit).all()


def get_user_session(db: Session, cookie_value: str):
    return db.query(models.Session).filter(models.Session.cookie == cookie_value).first()


def add_inventory_item(db: Session, product_description: str, supplier_id: int, stock: int, restock_limit: int):
    new_product = models.InventoryItem(description=product_description, supplierID=supplier_id, stock=stock,
                                       restockLimit=restock_limit, image=None)
    db.add(new_product)
    db.commit()


def add_to_stock(db: Session, product_id: int, amount: int):
    inventory_item = db.query(models.InventoryItem).filter(models.InventoryItem.productID == product_id).first()
    inventory_item.stock = inventory_item.stock + amount
    db.commit()


def set_delivery_confirmed(db: Session, delivery_id):
    delivery = db.query(models.Delivery).filter(models.Delivery.deliveryID == delivery_id).first()
    delivery.delivered = True
    db.commit()
