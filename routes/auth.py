from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import mongo
from datetime import datetime

auth_bp = Blueprint("auth_bp", __name__)

# --- User Login ---
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()

        if not email or not password:
            flash("Please enter both email and password!")
            return render_template("login.html")

        user = mongo.db.users.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["username"] = user.get("username", "User")
            session["is_admin"] = user.get("is_admin", False)

            if user.get("is_admin"):
                return redirect(url_for("admin_bp.dashboard"))
            return redirect(url_for("products_bp.list_products"))  # <-- go to product/shop page
        else:
            flash("Invalid credentials!")

    return render_template("login.html")


# --- User Register ---
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        age = request.form.get("age", "").strip()
        dob = request.form.get("dob", "").strip()
        raw_password = request.form.get("password", "").strip()

        if not name or not email or not raw_password:
            flash("⚠️ Name, Email, and Password are required!")
            return render_template("register.html")

        password = generate_password_hash(raw_password)

        existing = mongo.db.users.find_one({"email": email})
        if existing:
            flash("⚠️ Email already registered!")
            return redirect(url_for("auth_bp.register"))

        mongo.db.users.insert_one({
            "username": name,
            "email": email,
            "phone": phone,
            "address": address,
            "age": int(age) if age else None,
            "dob": dob,
            "profile_pic": None,
            "password": password,
            "score": 0,
            "created_at": datetime.now(),
            "is_admin": False
        })

        flash("✅ Registration successful. Please login.")
        return redirect(url_for("auth_bp.login"))

    return render_template("register.html")


# --- User Logout ---
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("auth_bp.login"))

