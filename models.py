from extensions import mongo
from datetime import datetime
from bson.objectid import ObjectId

# --- Collections ---
users_collection = lambda: mongo.db.users
fertilizers_collection = lambda: mongo.db.fertilizers
orders_collection = lambda: mongo.db.orders

# --- Helper Functions ---

# Users
def create_user(email, password, is_admin=False):
    return users_collection().insert_one({
        "email": email,
        "password": password,
        "is_admin": is_admin
    })

def find_user_by_email(email):
    return users_collection().find_one({"email": email})

def find_user_by_id(user_id):
    return users_collection().find_one({"_id": ObjectId(user_id)})


# Fertilizers (Products)
def create_fertilizer(name, description, category, price, stock_qty, main_image=None, gallery=None):
    """
    gallery: list of image filenames
    """
    return fertilizers_collection().insert_one({
        "name": name,
        "description": description,
        "category": category,
        "price": float(price),
        "stock_qty": int(stock_qty),
        "main_image": main_image,
        "gallery": gallery or []
    })

def get_all_fertilizers():
    return list(fertilizers_collection().find())

def find_fertilizer_by_id(fertilizer_id):
    return fertilizers_collection().find_one({"_id": ObjectId(fertilizer_id)})

def delete_fertilizer(fertilizer_id):
    return fertilizers_collection().delete_one({"_id": ObjectId(fertilizer_id)})


# Orders
def create_order(user_id, fertilizer_id, quantity):
    fertilizer = find_fertilizer_by_id(fertilizer_id)
    if not fertilizer:
        return None

    total_amount = quantity * fertilizer.get("price", 0)

    return orders_collection().insert_one({
        "user_id": ObjectId(user_id),
        "fertilizer_id": ObjectId(fertilizer_id),
        "fertilizer_name": fertilizer.get("name"),
        "quantity": quantity,
        "price": fertilizer.get("price"),
        "total_amount": total_amount,
        "status": "Pending",
        "ordered_at": datetime.utcnow()
    })

def get_orders_by_user(user_id):
    return list(orders_collection().find({"user_id": ObjectId(user_id)}))

def get_all_orders():
    return list(orders_collection().find())
