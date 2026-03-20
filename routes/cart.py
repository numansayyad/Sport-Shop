from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from bson.objectid import ObjectId
from extensions import mongo
from datetime import datetime

cart_bp = Blueprint("cart_bp", __name__, url_prefix="/cart")


# --- Add to Cart ---
@cart_bp.route("/add/<product_id>", methods=["GET", "POST"])
def add_to_cart(product_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first!", "warning")
        return redirect(url_for("auth_bp.login"))

    product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for("products_bp.list_products"))

    # Check if product already in cart
    existing = mongo.db.carts.find_one({
        "user_id": user_id,
        "product_id": product_id
    })

    if existing:
        # Increment quantity
        mongo.db.carts.update_one(
            {"_id": existing["_id"]},
            {"$inc": {"quantity": 1}}
        )
    else:
        # Add new item
        mongo.db.carts.insert_one({
            "user_id": user_id,
            "product_id": product_id,
            "quantity": 1,
            "added_at": datetime.now()
        })

    flash(f"{product['name']} added to cart!", "success")
    return redirect(url_for("cart_bp.view_cart"))


# --- View Cart ---
@cart_bp.route("/")
def view_cart():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first!", "warning")
        return redirect(url_for("auth_bp.login"))

    cart_items = list(mongo.db.carts.find({"user_id": user_id}))

    # Attach product details
    for item in cart_items:
        product = mongo.db.products.find_one({"_id": ObjectId(item["product_id"])})
        item["product_name"] = product.get("name") if product else "Unknown"
        item["price"] = product.get("price") if product else 0
        item["main_image"] = product.get("main_image") if product else None
        item["total"] = item["quantity"] * item["price"]

    # Total cart amount
    total_amount = sum(item["total"] for item in cart_items)

    return render_template("cart.html", cart_items=cart_items, total_amount=total_amount)


# --- Update Quantity ---
@cart_bp.route("/update/<cart_id>", methods=["POST"])
def update_cart(cart_id):
    quantity = int(request.form.get("quantity", 1))
    if quantity < 1:
        quantity = 1

    mongo.db.carts.update_one(
        {"_id": ObjectId(cart_id)},
        {"$set": {"quantity": quantity}}
    )

    flash("Cart updated successfully!", "success")
    return redirect(url_for("cart_bp.view_cart"))


# --- Remove Item ---
@cart_bp.route("/remove/<cart_id>")
def remove_from_cart(cart_id):
    mongo.db.carts.delete_one({"_id": ObjectId(cart_id)})
    flash("Item removed from cart!", "success")
    return redirect(url_for("cart_bp.view_cart"))


# --- Checkout ---
@cart_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first!", "warning")
        return redirect(url_for("auth_bp.login"))

    cart_items = list(mongo.db.carts.find({"user_id": user_id}))
    if not cart_items:
        flash("Your cart is empty!", "info")
        return redirect(url_for("products_bp.list_products"))

    # --- POST: Place Order ---
    if request.method == "POST":
        order_items = []
        total_amount = 0

        for item in cart_items:
            product = mongo.db.products.find_one({"_id": ObjectId(item["product_id"])})
            if not product:
                continue
            amount = item["quantity"] * product.get("price", 0)
            total_amount += amount
            order_items.append({
                "product_id": item["product_id"],
                "name": product.get("name"),
                "price": product.get("price"),
                "quantity": item["quantity"],
                "total": amount
            })

        order = {
            "user_id": user_id,
            "items": order_items,
            "total_amount": total_amount,
            "status": "Pending",
            "ordered_at": datetime.now()
        }

        mongo.db.orders.insert_one(order)
        mongo.db.carts.delete_many({"user_id": user_id})

        flash("Order placed successfully!", "success")
        return redirect(url_for("orders_bp.my_orders"))

    # --- GET: Redirect to review_order ---
    # Redirect to review_order page with first product in cart
    first_item = cart_items[0]
    return redirect(url_for("order_bp.review_order", product_id=first_item["product_id"], quantity=first_item["quantity"]))

# --- Buy Now ---
@cart_bp.route("/buy_now/<product_id>", methods=["GET", "POST"])
def buy_now(product_id):
    # Fetch product
    product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for("shop_bp.list_products"))  # replace with your products page route

    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first!", "warning")
        return redirect(url_for("auth_bp.login"))

    if request.method == "POST":
        quantity = int(request.form.get("quantity", 1))
        if quantity < 1:
            quantity = 1

        # Check if product already in cart
        existing = mongo.db.carts.find_one({"user_id": user_id, "product_id": product_id})
        if existing:
            mongo.db.carts.update_one({"_id": existing["_id"]}, {"$inc": {"quantity": quantity}})
        else:
            mongo.db.carts.insert_one({
                "user_id": user_id,
                "product_id": product_id,
                "quantity": quantity,
                "added_at": datetime.now()
            })

        flash(f"{product['name']} added to cart!", "success")
        return redirect(url_for("cart_bp.view_cart"))

    # GET → render template with product variable
    return render_template("buy_now.html", product=product)

