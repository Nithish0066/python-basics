from unicodedata import category

from flask import Flask, render_template, session, redirect, url_for, request, flash
from extensions import db
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import Product, User, Order, OrderItem
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "user_login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- ROLE SELECTION ----------------
@app.route("/")
def role_selection():
    return render_template("role_select.html")


# ---------------- USER REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = generate_password_hash(request.form.get("password"))

        new_user = User(username=username, email=email, password=password, role="user")
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.")
        return redirect(url_for("user_login"))

    return render_template("register.html")


# ---------------- USER LOGIN ----------------
@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email, role="user").first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Invalid User Credentials")

    return render_template("user_login.html")


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        admin = User.query.filter_by(email=email, role="admin").first()

        if admin and check_password_hash(admin.password, password):
            login_user(admin)
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid Admin Credentials")

    return render_template("admin_login.html")


# ---------------- USER HOME ----------------
@app.route("/home")
@login_required
def home():
    if current_user.role != "user":
        return redirect(url_for("admin_dashboard"))

    selected_category = request.args.get("category")

    if selected_category and selected_category != "All":
        products = Product.query.filter_by(category=selected_category).all()
    else:
        products = Product.query.all()

    # Get distinct categories for dropdown
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories]

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        selected_category=selected_category
    )
# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    users = User.query.all()
    products = Product.query.all()
    return render_template("admin.html", users=users, products=products)


# ---------------- ADD TO CART ----------------
@app.route("/add_to_cart/<int:product_id>")
@login_required
def add_to_cart(product_id):
    if current_user.role != "user":
        return redirect(url_for("admin_dashboard"))

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session["cart"] = cart

    return redirect(url_for("home"))


# ---------------- CART ----------------
@app.route("/cart")
@login_required
def cart():
    if current_user.role != "user":
        return redirect(url_for("admin_dashboard"))

    cart = session.get("cart", {})
    products = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            subtotal = product.price * quantity
            total += subtotal
            products.append({"product": product, "quantity": quantity, "subtotal": subtotal})

    return render_template("cart.html", products=products, total=total)


# ---------------- CHECKOUT ----------------
@app.route("/checkout")
@login_required
def checkout():

    cart = session.get("cart", {})

    if not cart:
        flash("Cart is empty")
        return redirect(url_for("home"))

    total = 0

    # Create new order first
    new_order = Order(
        user_id=current_user.id,
        total_amount=0
    )

    db.session.add(new_order)
    db.session.commit()

    # Add order items
    for product_id, quantity in cart.items():

        product = Product.query.get(int(product_id))

        if product:
            subtotal = product.price * quantity
            total += subtotal

            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=quantity
            )

            db.session.add(order_item)

    # Update total amount
    new_order.total_amount = total
    db.session.commit()

    # Clear cart
    session.pop("cart", None)

    flash("Order placed successfully!")
    return redirect(url_for("order_history"))
# ---------------- USER ORDER HISTORY ----------------
@app.route("/orders")
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template("orders.html", orders=orders)


# ---------------- PRODUCT DETAILS ----------------
@app.route("/product/<int:product_id>")
@login_required
def view_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return "Product Not Found"
    return render_template("product_details.html", product=product)


# ---------------- ADMIN ORDERS ----------------
@app.route("/admin/orders")
@login_required
def admin_orders():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    orders = Order.query.all()
    return render_template("admin_orders.html", orders=orders)

# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("role_selection"))

@app.route("/admin/add_product", methods=["GET", "POST"])
@login_required
def add_product():

    if current_user.role != "admin":
        return redirect(url_for("home"))

    if request.method == "POST":

        # 🔹 Get form data
        name = request.form.get("name")
        description = request.form.get("description")
        price = float(request.form.get("price"))
        stock = int(request.form.get("stock"))
        category = request.form.get("category")

        image_file = request.files.get("image")
        filename = None

        if image_file and image_file.filename != "":
            from werkzeug.utils import secure_filename
            import os

            upload_folder = os.path.join(app.root_path, "static/uploads")

            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            filename = secure_filename(image_file.filename)
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)

        # 🔹 Create Product
        new_product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            image=filename,
            category=category
        )

        db.session.add(new_product)
        db.session.commit()

        flash("Product Added Successfully")
        return redirect(url_for("admin_dashboard"))

    return render_template("add_product.html")
@app.route("/admin/delete_product/<int:product_id>")
@login_required
def delete_product(product_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    product = Product.query.get(product_id)

    if product:
        db.session.delete(product)
        db.session.commit()
        flash("Product Deleted Successfully")

    return redirect(url_for("admin_dashboard"))
@app.route("/admin/edit_product/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):

    if current_user.role != "admin":
        return redirect(url_for("home"))

    product = Product.query.get_or_404(product_id)

    if request.method == "POST":

        product.name = request.form.get("name")
        product.description = request.form.get("description")
        product.price = float(request.form.get("price"))
        product.stock = int(request.form.get("stock"))
        product.category = request.form.get("category")

        # If new image uploaded
        image_file = request.files.get("image")
        if image_file and image_file.filename != "":
            image_path = os.path.join("static/uploads", image_file.filename)
            image_file.save(image_path)
            product.image = image_file.filename

        db.session.commit()
        flash("Product updated successfully")

        return redirect(url_for("admin_dashboard"))

    return render_template("edit_product.html", product=product)
@app.route("/remove_from_cart/<int:product_id>")
@login_required
def remove_from_cart(product_id):

    if "cart" in session:
        cart = session["cart"]

        if str(product_id) in cart:
            del cart[str(product_id)]

        session["cart"] = cart

    return redirect(url_for("cart"))


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email="admin@gmail.com").first():
            admin = User(
                username="admin",
                email="admin@gmail.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)