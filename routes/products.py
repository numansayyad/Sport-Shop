from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from bson.objectid import ObjectId
from extensions import mongo
from werkzeug.utils import secure_filename
import os
import json

# --- Blueprint ---
products_bp = Blueprint("products_bp", __name__)

# ---------------------------
# --- USER SIDE ROUTES ------
# ---------------------------

# --- List All Products (Shop Page) ---
@products_bp.route("/")
def list_products():
    # Fetch products and categories
    products = list(mongo.db.products.find())
    
    # Ensure all products have required fields
    for p in products:
        p.setdefault("category", "Uncategorized")
        p.setdefault("main_image", "")
        p.setdefault("extra_images", [])
    
    categories = mongo.db.products.distinct("category")
    categories = sorted(categories)
    
    return render_template("products.html", products=products, categories=categories)

# --- Product Details ---
@products_bp.route("/product/<product_id>")
def product_details(product_id):
    product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return "Product not found", 404
    
    # Ensure fields exist
    product.setdefault("main_image", "")
    product.setdefault("extra_images", [])
    product.setdefault("category", "Uncategorized")
    
    return render_template("product_details.html", product=product)

# ---------------------------
# --- ADMIN SIDE ROUTES -----
# ---------------------------

# --- Admin Products Page ---
@products_bp.route("/admin/products")
def admin_products():
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))
    
    products = list(mongo.db.products.find())
    categories = mongo.db.products.distinct("category")
    
    # Ensure defaults
    for p in products:
        p.setdefault("category", "Uncategorized")
        p.setdefault("main_image", "")
        p.setdefault("extra_images", [])
    
    return render_template("admin/products.html", products=products, categories=categories)

# --- Save (Add / Update) Product ---
@products_bp.route("/admin/products/save", methods=["POST"])
def save_product():
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    product_id = request.form.get("product_id")
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    price = float(request.form.get("price", 0))
    stock = int(request.form.get("stock", 0))
    category = request.form.get("category", "").strip()

    # --- Handle main image ---
    main_image_file = request.files.get("main_image")
    
    # --- Handle extra images ---
    extra_images_files = request.files.getlist("extra_images")

    update_data = {
        "name": name,
        "description": description,
        "price": price,
        "stock": stock,
        "category": category
    }

    # Save images folder path
    upload_dir = os.path.join(current_app.root_path, "static/uploads")
    os.makedirs(upload_dir, exist_ok=True)

    if product_id:  # UPDATE
        product = mongo.db.products.find_one({"_id": ObjectId(product_id)})

        # Main image
        if main_image_file and main_image_file.filename:
            filename = secure_filename(main_image_file.filename)
            main_image_file.save(os.path.join(upload_dir, filename))
            update_data["main_image"] = "uploads/" + filename
        else:
            update_data["main_image"] = product.get("main_image", "")

        # Extra images
        saved_extra_images = product.get("extra_images", [])
        if extra_images_files and any(f.filename for f in extra_images_files):
            for f in extra_images_files:
                if f.filename:
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(upload_dir, filename))
                    saved_extra_images.append("uploads/" + filename)
        update_data["extra_images"] = saved_extra_images

        mongo.db.products.update_one({"_id": ObjectId(product_id)}, {"$set": update_data})
        flash("Product updated successfully", "success")
    else:  # ADD NEW
        # Main image
        if main_image_file and main_image_file.filename:
            filename = secure_filename(main_image_file.filename)
            main_image_file.save(os.path.join(upload_dir, filename))
            update_data["main_image"] = "uploads/" + filename
        else:
            update_data["main_image"] = ""

        # Extra images
        saved_extra_images = []
        if extra_images_files and any(f.filename for f in extra_images_files):
            for f in extra_images_files:
                if f.filename:
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(upload_dir, filename))
                    saved_extra_images.append("uploads/" + filename)
        update_data["extra_images"] = saved_extra_images

        mongo.db.products.insert_one(update_data)
        flash("Product added successfully", "success")

    return redirect(url_for("products_bp.admin_products"))

# --- Delete Product ---
@products_bp.route("/admin/products/delete/<product_id>")
def delete_product(product_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))
    
    mongo.db.products.delete_one({"_id": ObjectId(product_id)})
    flash("Product deleted successfully", "success")
    return redirect(url_for("products_bp.admin_products"))
