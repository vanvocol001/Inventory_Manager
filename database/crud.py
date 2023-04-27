from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc

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


def add_supplier(db: Session, name: str, address: str):
    new_supplier = models.Supplier(name=name, address=address)
    db.add(new_supplier)
    db.commit()


def add_to_stock(db: Session, product_id: int, amount: int):
    inventory_item = db.query(models.InventoryItem).filter(models.InventoryItem.productID == product_id).first()
    inventory_item.stock = inventory_item.stock + amount
    db.commit()


def subtract_from_stock(db: Session, product_id: int, amount: int):
    inventory_item = db.query(models.InventoryItem).filter(models.InventoryItem.productID == product_id).first()
    inventory_item.stock = max(inventory_item.stock - amount, 0)
    db.commit()


def add_delivery(db: Session, date: str, supplier_id: int, products: List[int], stock: List[int]):
    new_delivery = models.Delivery(dateExpected=date, supplierID=supplier_id)
    db.add(new_delivery)
    db.flush()
    delivery_id = new_delivery.deliveryID

    orders = []
    for product_id, quantity in zip(products, stock):
        order = models.InventoryOrder(deliveryID=delivery_id, productID=product_id, quantityOrdered=quantity)
        orders.append(order)
    db.bulk_save_objects(orders)
    db.commit()


def set_delivery_confirmed(db: Session, delivery_id):
    delivery = db.query(models.Delivery).filter(models.Delivery.deliveryID == delivery_id).first()
    delivery.delivered = True
    db.commit()


def add_transaction(db: Session, products: List[int], stock: List[int]):
    new_transaction = models.Transaction()
    db.add(new_transaction)
    db.flush()
    transaction_id = new_transaction.transactionID

    items = []
    for product_id, quantity in zip(products, stock):
        item = models.TransactionReport(transactionID=transaction_id, productID=product_id, quantitySold=quantity)
        items.append(item)
    db.bulk_save_objects(items)
    db.commit()


def add_disposal(db: Session, user_id: str, reason: str, products: List[int], stock: List[int]):
    new_disposal = models.DisposedInventory(reason=reason, userID=user_id)
    db.add(new_disposal)
    db.flush()
    disposal_id = new_disposal.disposalID

    items = []
    for ind in range(0, len(products)):
        item = models.DisposedInventoryReport(disposalID=disposal_id, productID=products[0], quantityDisposed=stock[0])
        items.append(item)
    db.bulk_save_objects(items)
    db.commit()
