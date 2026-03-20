from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from bson.objectid import ObjectId
from datetime import datetime
from extensions import mongo

order_bp = Blueprint("order_bp", __name__, url_prefix="/orders")

# --- Step 1: Place an Order (Enter Quantity) ---
@order_bp.route("/place/<product_id>", methods=["GET", "POST"])
def place_order(product_id):
    product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for("shop_bp.list_products"))

    if request.method == "POST":
        quantity = int(request.form.get("quantity", 1))
        if quantity <= 0:
            flash("Invalid quantity!", "warning")
            return redirect(request.url)

        # Redirect to review page with quantity as query param
        return redirect(url_for("order_bp.review_order", product_id=product_id, quantity=quantity))

    return render_template("place_order.html", product=product)


# --- Step 2: Review Order and Select Payment ---
@order_bp.route("/payment")
def payment_page():
    product_id = request.args.get('product_id')
    quantity = int(request.args.get('quantity', 1))
    total_amount = float(request.args.get('total_amount', 0))
    
    if not product_id or quantity <= 0:
        flash("Invalid order details", "danger")
        return redirect(url_for("products_bp.list_products"))
    
    product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        flash("Product not found", "danger")
        return redirect(url_for("products_bp.list_products"))
    
    if product.get('main_image'):
        image_url = url_for('static', filename=f'uploads/{product.get("main_image").split("/")[-1]}')
    else:
        image_url = url_for('static', filename='images/image.png')
    
    return render_template("payment.html", 
                         product_id=product_id, 
                         quantity=quantity, 
                         total_amount=total_amount,
                         product_name=product.get('name', 'Product'),
                         image=image_url)

@order_bp.route("/review/<product_id>", methods=["GET", "POST"])
def review_order(product_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first!", "warning")
        return redirect(url_for("auth_bp.login"))

    # Check if redirected from checkout (cart items)
    cart_items = list(mongo.db.carts.find({"user_id": user_id}))
    is_cart_checkout = False

    if cart_items:
        # Check if product_id is "cart" to indicate full cart review
        if product_id == "cart":
            is_cart_checkout = True
            items = []
            total_amount = 0
            for item in cart_items:
                product = mongo.db.products.find_one({"_id": ObjectId(item["product_id"])})
                if not product:
                    continue
                total = item["quantity"] * float(product.get("price", 0))
                total_amount += total
                items.append({
                    "product_id": item["product_id"],
                    "name": product.get("name"),
                    "price": float(product.get("price", 0)),
                    "quantity": item["quantity"],
                    "total": total,
                    "main_image": product.get("main_image"),
                    "category": product.get("category"),
                    "description": product.get("description")
                })

            if request.method == "POST":
                # Check stock for all cart items
                insufficient_items = []
                for item in items:
                    prod = mongo.db.products.find_one({"_id": ObjectId(item["product_id"])})
                    if prod.get("stock_qty", 0) < item["quantity"]:
                        insufficient_items.append(item["name"])

                if insufficient_items:
                    flash("Stock Not Available for: " + ', '.join(insufficient_items), "danger")
                    return render_template("review_order.html", cart_items=items, total_amount=total_amount, is_cart=True)

                # Deduct stock for all items
                for item in items:
                    mongo.db.products.update_one({"_id": ObjectId(item["product_id"])}, {"$inc": {"stock_qty": -item["quantity"]}})

                # Place order for all cart items
                payment_method = request.form.get("payment_method", "offline")
                order = {
                    "user_id": user_id,
                    "items": items,
                    "total_amount": total_amount,
                    "payment_method": payment_method,
                    "status": "Paid" if payment_method == "online" else "Pending",
                    "ordered_at": datetime.now()
                }
                # Add loyalty points: 10 per product + 5 per ₹100
                points_earned = len(items) * 10 + int(total_amount // 20)
                mongo.db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$inc": {"score": points_earned}}
                )
                
                mongo.db.orders.insert_one(order)
                # Clear cart
                mongo.db.carts.delete_many({"user_id": user_id})
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        "success": True, 
                        "message": f"Cart order placed successfully!", 
                        "total": total_amount,
                        "points": points_earned
                    })
                flash(f"Order placed successfully! Total: ₹{total_amount} (+{points_earned} points)", "success")
                return redirect(url_for("order_bp.my_orders"))

            return render_template("review_order.html", cart_items=items, total_amount=total_amount, is_cart=True)

    # Single product flow (buy now)
    quantity = int(request.args.get("quantity", 1))
    product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for("shop_bp.list_products"))

    total_amount = quantity * float(product.get("price", 0))

    if request.method == "POST":
        # Check stock before placing order (single product)
        if product.get("stock_qty", 0) < quantity:
            flash("Stock Not Available", "danger")
            return render_template("review_order.html", product=product, quantity=quantity, total_amount=total_amount, is_cart=False)

        # Deduct stock
        mongo.db.products.update_one({"_id": ObjectId(product_id)}, {"$inc": {"stock_qty": -quantity}})

        payment_method = request.form.get("payment_method")

        # Online/Offline Payment - Unified
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)} )
        username = user.get("username", "Unknown") if user else "Unknown"
        phone = user.get("phone", "N/A") if user else "N/A"

        order = {
            "user_id": user_id,
            "username": username,
            "phone": phone,
            "product_id": product_id,
            "product_name": product.get("name"),
            "quantity": quantity,
            "price": float(product.get("price", 0)),
            "total_amount": total_amount,
            "payment_method": payment_method,
            "status": "Paid" if payment_method == "online" else "Pending",
            "ordered_at": datetime.now()
        }
        
        # Add loyalty points
        points_earned = 10 + int(total_amount // 20)
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"score": points_earned}}
        )
        
        mongo.db.orders.insert_one(order)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "success": True, 
                "message": f"Order placed successfully via COD!", 
                "total": total_amount,
                "points": points_earned
            })
        
        flash(f"Order placed successfully! Total: ₹{total_amount} (+{points_earned} points)", "success")
        return redirect(url_for("order_bp.my_orders"))

    return render_template("review_order.html", product=product, quantity=quantity, total_amount=total_amount, is_cart=False)

# --- Delete an Order ---
@order_bp.route("/delete/<order_id>")
def delete_order(order_id):
    mongo.db.orders.delete_one({"_id": ObjectId(order_id)})
    flash("Order deleted successfully!", "success")
    return redirect(url_for("order_bp.my_orders"))


# --- My Orders Page ---
@order_bp.route("/my_orders")
def my_orders():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first.", "warning")
        return redirect(url_for("auth_bp.login"))

    orders = list(mongo.db.orders.find({"user_id": user_id}).sort("ordered_at", -1))

    for o in orders:
        product_id = o.get("product_id")
        if product_id:
            product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
            o["product_name"] = product.get("name") if product else "Unknown"
            o["price"] = float(product.get("price", 0)) if product else 0
            o["main_image"] = product.get("main_image") if product else None
            o["total_amount"] = o.get("quantity", 1) * o["price"]
        else:
            o["product_name"] = "Unknown Product"
            o["price"] = 0
            o["main_image"] = None
            o["total_amount"] = 0

    return render_template("my_orders.html", orders=orders)
