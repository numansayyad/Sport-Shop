# from flask import Flask, render_template
# from extensions import mongo
# from routes.auth import auth_bp
# from routes.products import products_bp
# from routes.orders import order_bp
# from routes.admin import admin_bp
# from routes.cart import cart_bp
# from routes.profile import profile_bp



# def create_app():
#     app = Flask(__name__)

#     # --- App Config ---
#     app.config["SECRET_KEY"] = "fertilizer123"  # change in production
#     app.config["MONGO_URI"] = "mongodb://localhost:27017/sports_shop"

#     # --- Init MongoDB ---
#     mongo.init_app(app)

#     # --- Register Blueprints ---
#     app.register_blueprint(auth_bp, url_prefix="/auth")
#     app.register_blueprint(products_bp, url_prefix="/products")
#     app.register_blueprint(order_bp, url_prefix="/order")
#     app.register_blueprint(admin_bp, url_prefix="/admin")
#     app.register_blueprint(cart_bp,  url_prefix="/cart")
#     app.register_blueprint(profile_bp, url_prefix="/profile")

#     # --- Homepage ---
#     @app.route("/")
#     def home():
#         products = list(mongo.db.products.find().limit(4))  # get top 4 products
#         return render_template("index.html", products=products)
#     return app


# if __name__ == "__main__":
#     app = create_app()
#     app.run(debug=True)


from flask import Flask, render_template
from extensions import mongo
from routes.auth import auth_bp
from routes.products import products_bp
from routes.orders import order_bp
from routes.admin import admin_bp
from routes.cart import cart_bp
from routes.profile import profile_bp


def create_app():
    app = Flask(__name__)

    # --- App Config ---
    app.config["SECRET_KEY"] = "fertilizer123"

    # app.config["MONGO_URI"] =" mongodb+srv://sayyadnuman154_db_user:<bR6UMmS9bkWn8mAS>@sportcluster.yylsqqr.mongodb.net/?appName=sportCluster"
    app.config["MONGO_URI"] = "mongodb+srv://sayyadnuman154_db_user:bR6UMmS9bkWn8mAS@sportcluster.yylsqqr.mongodb.net/sports_shop"
    # --- Init MongoDB ---
    mongo.init_app(app)

    # --- Register Blueprints ---
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(order_bp, url_prefix="/order")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(profile_bp, url_prefix="/profile")

    # --- Homepage ---
    @app.route("/")
    def home():
        products = list(mongo.db.products.find().limit(4))
        return render_template("index.html", products=products)

    return app


# ✅ Required for Render
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)