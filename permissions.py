import configparser
import os


def load_config():
    if not os.path.isfile("database/config.ini"):
        create_config()
    config = configparser.ConfigParser()
    config.read("database/config.ini")
    return config


def get_permissions():
    return config["STORED"]


def update_config(perm_dict):
    for perm, value in perm_dict.items():
        config["STORED"][perm] = value
    write_config(config)


def write_config(config):
    with open("database/config.ini", "w") as config_file:
        config.write(config_file)


def create_config():
    default_config = configparser.ConfigParser()
    default_config["DEFAULT"] = {
            "ProductCreate": 5,
            "DeliveryCreate": 5,
            "DeliveryConfirm": 0,
            "DeliveryReject": 5,
            "DisposalCreate": 5,
            "TransactionCreate": 0,
            "SupplierCreate": 10
        }
    default_config["STORED"] = {
            "ProductCreate": 5,
            "DeliveryCreate": 5,
            "DeliveryConfirm": 0,
            "DeliveryReject": 5,
            "DisposalCreate": 5,
            "TransactionCreate": 0,
            "SupplierCreate": 10
        }

    write_config(default_config)


def verify_permission(perm_name: str, account_level: int):
    return account_level >= int(config["STORED"][perm_name])


config = load_config()
