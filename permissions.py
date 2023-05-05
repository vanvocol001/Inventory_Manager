from database import crud
from sqlalchemy.orm import Session


def load_config(db: Session):
    permission_row = crud.load_permissions(db)
    config = {
        "ProductCreate": permission_row.productCreate,
        "DeliveryCreate": permission_row.deliveryCreate,
        "DeliveryConfirm": permission_row.deliveryConfirm,
        "DeliveryReject": permission_row.deliveryReject,
        "DisposalCreate": permission_row.disposalCreate,
        "TransactionCreate": permission_row.transactionCreate,
        "SupplierCreate": permission_row.supplierCreate
    }
    return config


def update_config(perm_dict):
    for perm, value in perm_dict.items():
        config["STORED"][perm] = value
    write_config(config)
