from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from extensions import mongo
import os
from datetime import datetime
import json


admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")

# ---------------- Admin Login ----------------
@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Enter both email and password", "warning")
            return render_template("admin/admin_login.html")

        admin = mongo.db.admins.find_one({"email": email})
        if admin and admin.get("password") == password:
            session["is_admin"] = True
            session["admin_email"] = email
            flash("Login successful!", "success")
            return redirect(url_for("admin_bp.dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("admin/admin_login.html")


# ---------------- Admin Logout ----------------
@admin_bp.route("/logout")
def logout():
    session.pop("is_admin", None)
    session.pop("admin_email", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("admin_bp.admin_login"))


# ---------------- Dashboard ----------------
@admin_bp.route("/")
def dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    product_count = mongo.db.products.count_documents({})
    user_count = mongo.db.users.count_documents({})
    order_count = mongo.db.orders.count_documents({})

    return render_template(
        "admin/dashboard.html",
        product_count=product_count,
        user_count=user_count,
        order_count=order_count
    )


# ---------------- Manage Products ----------------
@admin_bp.route("/products", methods=["GET", "POST"])
def manage_products():
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    if request.method == "POST":
        product_id = request.form.get("product_id")
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        stock_qty = int(request.form.get("stock_qty", 0))
        category = request.form.get("category", "").strip()
        price = float(request.form.get("price", 0))

        # --- Handle multiple images ---
        images_files = request.files.getlist("images")  # multiple files
        existing_images = request.form.get("existing_images", "[]")
        existing_images = json.loads(existing_images) if existing_images else []

        saved_images = existing_images.copy()

        for f in images_files:
            if f and f.filename != "":
                fname = secure_filename(f.filename)
                save_path = os.path.join(current_app.root_path, "static", "uploads", fname)
                f.save(save_path)
                saved_images.append(fname)

        # --- Set main image as first image in the list ---
        main_image_path = saved_images[0] if saved_images else ""

        product_data = {
            "name": name,
            "description": description,
            "price": price,
            "stock_qty": stock_qty,
            "category": category,
            "main_image": main_image_path,
            "images": saved_images  # ✅ Store all images
        }

        if product_id:  # Update existing product
            mongo.db.products.update_one({"_id": ObjectId(product_id)}, {"$set": product_data})
            flash("Product updated successfully", "success")
        else:  # Add new product
            mongo.db.products.insert_one(product_data)
            flash("Product added successfully", "success")

        return redirect(url_for("admin_bp.manage_products"))

    # --- GET Products ---
    q = request.args.get("q", "").strip()
    query = {}
    if q:
        query = {"$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"category": {"$regex": q, "$options": "i"}}
        ]}
    products = list(mongo.db.products.find(query))

    # Ensure every product has 'images' key
    for p in products:
        if "images" not in p or not p["images"]:
            p["images"] = []

    categories = mongo.db.products.distinct("category")
    return render_template("admin/products.html", products=products, categories=categories)

# ---------------- Delete Product ----------------
@admin_bp.route("/products/delete/<product_id>")
def delete_product(product_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    mongo.db.products.delete_one({"_id": ObjectId(product_id)})
    flash("Product deleted successfully", "success")
    return redirect(url_for("admin_bp.manage_products"))


# ---------------- Manage Users ----------------
@admin_bp.route("/users")
def manage_users():
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    q = request.args.get("q", "").strip()
    query = {}
    if q:
        query = {"$or": [
            {"username": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
            {"phone": {"$regex": q, "$options": "i"}},
            {"address": {"$regex": q, "$options": "i"}}
        ]}
    users = list(mongo.db.users.find(query))
    return render_template("admin/users.html", users=users)


# ---------------- Manage Orders ----------------
@admin_bp.route("/orders", methods=["GET", "POST"])
def manage_orders():
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    orders = list(mongo.db.orders.find().sort("ordered_at", -1))

    # Populate user and product info
    for o in orders:
        user = mongo.db.users.find_one({"_id": ObjectId(o["user_id"])}) if "user_id" in o else None
        product = mongo.db.products.find_one({"_id": ObjectId(o["product_id"])}) if "product_id" in o else None
        o["username"] = user["username"] if user else "Unknown"
        o["product_name"] = product["name"] if product else "Unknown"
        o["quantity"] = o.get("quantity", 1)
        o["status"] = o.get("status", "Pending")
        o["ordered_at"] = o.get("ordered_at")

    return render_template("admin/orders.html", orders=orders)


# ---------------- Update Order Status ----------------
@admin_bp.route("/orders/update_status", methods=["POST"])
def update_order_status():
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    order_ids = request.form.getlist("order_ids")
    print("Order IDs:", order_ids)  # debug

    for oid in order_ids:
        status = request.form.get(f"status_{oid}", "Pending")
        print(f"Updating {oid} to {status}")  # debug
        mongo.db.orders.update_one({"_id": ObjectId(oid)}, {"$set": {"status": status}})

    flash("Order status updated successfully!", "success")
    return redirect(url_for("admin_bp.manage_orders"))
