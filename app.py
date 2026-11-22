from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
from flask_wtf.csrf import CSRFProtect


load_dotenv()

app = Flask(__name__)

csrf = CSRFProtect(app)

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set.")

app.secret_key = SECRET_KEY

starting_products = [
    {"id": 0, "name": "Monitor", "price": 1, "stock": 0, "image": "monitor1.jfif"},
    {"id": 1, "name": "Keyboard", "price": 100, "stock": 10, "image": "keyboard1.jfif"},
    {"id": 2, "name": "Mouse", "price": 200, "stock": 22, "image": "mouse1.webp"},
    {"id": 3, "name": "Motherboard-H110M", "price": 300, "stock": 33, "image": "H110M1.jpg"},
    {"id": 4, "name": "SSD", "price": 400, "stock": 44, "image": "SSD1.webp"},
    {"id": 5, "name": "Power Supply", "price": 500, "stock": 55, "image": "PSU1.webp"},
    {"id": 6, "name": "PC case", "price": 600, "stock": 66, "image": "pccase1.jpg"},
    {"id": 7, "name": "GPU-GTX1050", "price": 700, "stock": 77, "image": "GTX10501.jfif"},
    {"id": 8, "name": "CPU-G4560", "price": 800, "stock": 88, "image": "G45601.jfif"},
    {"id": 9, "name": "4GB RAM", "price": 900, "stock": 99, "image": "4GBRAM1.jfif"},
    {"id": 10, "name": "CPU Cooler", "price": 1000, "stock": 100, "image": "cpucooler1.webp"}
]

def get_db():
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        conn = psycopg2.connect(database_url, cursor_factory=DictCursor)
        return conn

    conn = sqlite3.connect("store.db")
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(cursor, query, values):
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        query = query.replace("?", "%s")

    cursor.execute(query, values)

def create_tables():
    conn = get_db()
    cursor = conn.cursor()

    database_url = os.getenv("DATABASE_URL")
    id_column = "id SERIAL PRIMARY KEY" if database_url else "id INTEGER PRIMARY KEY AUTOINCREMENT"
    

    execute_query(cursor, f"""
        CREATE TABLE IF NOT EXISTS users2 (
            {id_column},
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
         )
    """,())

    execute_query(cursor, f"""
        CREATE TABLE IF NOT EXISTS orders2 (
            {id_column},
            user_id INTEGER,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """,())

    execute_query(cursor, f"""
        CREATE TABLE IF NOT EXISTS order_items2 (
            {id_column},
            order_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            subtotal REAL NOT NULL
        )
    """,())

    execute_query(cursor, """
        CREATE TABLE IF NOT EXISTS products2 (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            image TEXT NOT NULL
        )
    """, ())

    execute_query(cursor, "SELECT COUNT(*) AS total FROM products2", ())
    if cursor.fetchone()["total"] == 0:
        for p in starting_products:
            execute_query(cursor, "INSERT INTO products2 (id, name, price, stock, image) VALUES (?, ?, ?, ?, ?)",
                          (p["id"], p["name"], p["price"], p["stock"], p["image"]))

    conn.commit()
    conn.close()

create_tables()


@app.context_processor
def cart_count():
    cart = session.get("cart", {})
    return {"cart_count": sum(cart.values()), 
            "is_admin": admin_required()
    }

def get_all_products():
    conn = get_db()
    cursor = conn.cursor()
    execute_query(cursor, "SELECT * FROM products2 ORDER BY id", ())
    products = cursor.fetchall()
    conn.close()
    return products

def get_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    execute_query(cursor, "SELECT * FROM products2 WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

def admin_required():
    if "user_id" not in session:
        return False
    conn = get_db()
    cursor = conn.cursor()
    execute_query(cursor,"SELECT is_admin FROM users2 WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()
    conn.close()
    return user and user["is_admin"] == 1

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if len(password) < 4 or len(password) > 15: 
            flash("Password must be at least 8 to 15 characters")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        conn = get_db()
        cursor = conn.cursor()

        try:
            execute_query(cursor,
                "INSERT INTO users2 (name, email, password_hash) VALUES(?, ?, ?)",
                (name, email, password_hash)
            )
            conn.commit()
        except (sqlite3.IntegrityError, psycopg2.IntegrityError):
            conn.rollback()
            conn.close()
            flash("Email already registered")
            return redirect(url_for("register"))

        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        execute_query(cursor,"SELECT * FROM users2 WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("profile"))

        flash("Invalid email or password")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    return redirect(url_for("home"))

@app.route("/")
def home():
    return render_template("home.html", products2=get_all_products())

@app.route("/product/<int:product2_id>")
def product_detail(product2_id):
    product2 = get_product(product2_id)    
    if product2:
        return render_template("product.html", product2=product2) 
    return "Product not found", 404

@app.route("/search")
def search():
    query = request.args.get("search", "")

    results = []
    for product2 in get_all_products():
        if query.lower() in product2["name"].lower():
            results.append(product2)

    return render_template("search.html", results=results, query=query)

@app.route("/live") 
def live():
    return render_template("live.html")

@app.route("/place-order", methods=["POST"])
def place_order():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    name = request.form["name"]
    address = request.form["address"]

    cart_data2 = session.get("cart", {})
    user_id2 = session.get("user_id")

    if not cart_data2:
        return redirect(url_for("cart"))

    all_products = get_all_products()
    for product2 in all_products:
        key = str(product2["id"])
        if key in cart_data2 and cart_data2[key] > product2["stock"]:
            flash("Not enough stock for " + product2["name"])
            return redirect(url_for("cart"))

    cart_products2 = []
    for product2 in all_products:
        key = str(product2["id"])
        if key in cart_data2:
            quantity2 = cart_data2[key]
            subtotal2 = product2["price"] * quantity2
            cart_products2.append({
                "name": product2["name"],
                "price": product2["price"],
                "quantity": quantity2,
                "subtotal": subtotal2
            })

    total = 0
    for product2 in cart_products2:
        total += product2["subtotal"]

    conn = get_db()
    cursor = conn.cursor()

    try:
        execute_query(cursor,
            "INSERT INTO orders2 (user_id, name, address, total, status) VALUES (?, ?, ?, ?, ?) RETURNING id",
            (user_id2, name, address, total, "Pending")
        )
        order_id2 = cursor.fetchone()["id"]
    
        for product2 in cart_products2:
            execute_query(cursor,
                "INSERT INTO order_items2 (order_id, name, price, quantity, subtotal) VALUES (?, ?, ?, ?, ?)",
                (order_id2, product2["name"], product2["price"], product2["quantity"], product2["subtotal"]))

        for key, qty in cart_data2.items():
            execute_query(cursor,
                "UPDATE products2 SET stock = stock - ? WHERE id = ? AND stock >= ?",
                (qty, int(key), qty))
            if cursor.rowcount == 0:
                conn.rollback()
                flash("Not enough stock for an item. Please check your cart.")
                return redirect(url_for("cart"))
    
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    session.pop("cart", None)

    return redirect(url_for("order_confirmation", order_id=order_id2))

@app.route("/order/<int:order_id>")
def order_confirmation(order_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    execute_query(cursor,
                "SELECT * FROM orders2 WHERE id = ? AND user_id = ? ",
                (order_id, session["user_id"]))
    order = cursor.fetchone()

    if not order:
        conn.close()
        return "Order not found", 404

    execute_query(cursor, "SELECT * FROM order_items2 WHERE order_id = ?", (order_id,))
    items = cursor.fetchall()
    conn.close()

    order2 = {
        "total": order["total"],
        "products": items
    }

    return render_template(
        "order.html",
        order_id=order["id"],
        name=order["name"],
        address=order["address"],
        order2=order2
    )

@app.route("/admin")
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("login"))

    return render_template("admin_dashboard.html")

@app.route("/admin/orders") 
def admin_orders():
    if not admin_required():
        return redirect(url_for("login"))
    
    conn = get_db()
    cursor = conn.cursor()

    execute_query(cursor,"SELECT * FROM orders2 ORDER BY id DESC",())
    all_orders = cursor.fetchall()

    orders_with_items = []
    for order2 in all_orders:
        execute_query(cursor, "SELECT * FROM order_items2 WHERE order_id = ?", (order2["id"],))
        items2 = cursor.fetchall()
        orders_with_items.append({
            "id": order2["id"],
            "name": order2["name"],
            "address": order2["address"],
            "total": order2["total"],
            "status": order2["status"],
            "products": items2
        })

    conn.close()

    return render_template("admin_orders.html", orders2=orders_with_items)

@app.route("/admin/update-status/<int:order2_id>", methods=["POST"])
def update_status(order2_id):
    if not admin_required():
        return redirect(url_for("login"))

    new_status = request.form["status"]

    if new_status not in ["Pending", "Shipped", "Delivered"]:
        return redirect(url_for("admin_orders"))

    conn = get_db()
    cursor = conn.cursor()
    execute_query(cursor,"SELECT status FROM orders2 WHERE id = ?", (order2_id,))
    row = cursor.fetchone()

    steps = ["Pending", "Shipped", "Delivered"]
    if row and steps.index(new_status) < steps.index(row["status"]):
        conn.close()
        return redirect(url_for("admin_orders"))

    execute_query(cursor, "UPDATE orders2 SET status = ? WHERE id = ?", (new_status, order2_id))
    conn.commit()
    conn.close()

    flash("Product updated")
    return redirect(url_for("admin_orders"))

@app.route("/admin/products")
def admin_products():
    if not admin_required():
        return redirect(url_for("login"))

    return render_template("admin_products.html", products=get_all_products())

@app.route("/admin/products/<int:product_id>/edit", methods=["POST"])
def admin_edit_product(product_id):
    if not admin_required():
        return redirect(url_for("login"))

    name = request.form["name"].strip()
    price = float(request.form["price"])
    stock = int(request.form["stock"])
    image = request.form["image"].strip()

    if not name or not image or price < 0 or stock < 0:
        flash("Invalid values")
        return redirect(url_for("admin_products"))

    conn = get_db()
    cursor = conn.cursor()
    execute_query(cursor, 
                "UPDATE products2 SET name = ?, price = ?, stock = ?, image = ? WHERE id = ?",
                (name, price, stock, image, product_id))
    conn.commit()
    conn.close()

    flash("Product updated")
    return redirect(url_for("admin_products"))

@app.route("/admin/products/add", methods=["POST"])
def admin_add_product():
    if not admin_required():
        return redirect(url_for("login"))

    name = request.form["name"].strip()
    price = float(request.form["price"])
    stock = int(request.form["stock"])
    image = request.form["image"].strip()

    if not name or not image or price < 0 or stock < 0:
        flash("Invalid values")
        return redirect(url_for("admin_products"))


    conn = get_db()
    cursor = conn.cursor()
    execute_query(cursor, "SELECT COALESCE(MAX(id), -1) + 1 AS next_id FROM products2", ())
    next_id = cursor.fetchone()["next_id"]



    execute_query(cursor,
                "INSERT INTO products2 (id, name, price, stock, image) VALUES (?, ?, ?, ?, ?)",
                (next_id, name, price, stock, image))
    conn.commit()
    conn.close()

    flash("Product added")
    return redirect(url_for("admin_products"))

@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
def admin_delete_product(product_id):
    if not admin_required():
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()
    execute_query(cursor, "DELETE FROM products2 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

    flash("Product deleted")
    return redirect(url_for("admin_products"))

@app.route("/checkout")
def checkout():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    cart_data = session.get("cart", {})

    if not cart_data:   
        return redirect(url_for("cart"))

    return render_template("checkout.html")

@app.route("/add-to-cart/<int:product2_id>", methods=["POST"])
def add_to_cart(product2_id):
    cart = session.get("cart", {})
    key  = str(product2_id)

    product2 = get_product(product2_id)
    if product2 is None:
        return redirect(request.referrer or url_for("home"))

    current_qty = cart.get(key, 0)

    if current_qty >= product2["stock"]:
        flash("Sorry, no more stock for this item.")
        return redirect(request.referrer or url_for("home"))

    cart[key] = current_qty + 1
    session["cart"] = cart
    return redirect(request.referrer or url_for("cart"))

@app.route("/increase-quantity/<int:product2_id>", methods=["POST"])
def increase_quantity(product2_id):
    cart = session.get("cart", {})
    key = str(product2_id)

    product2 = get_product(product2_id)
    if product2 is None:
        return redirect(request.referrer or url_for("home"))

    current_qty = cart.get(key, 0)

    if current_qty >= product2["stock"]:
        flash("Sorry, no more stock for this item.")
        return redirect(request.referrer or url_for("cart"))
        
    cart[key] = current_qty + 1
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/decrease-quantity/<int:product2_id>", methods=["POST"])
def decrease_quantity(product2_id):
    cart = session.get("cart", {})
    key = str(product2_id)

    if key in cart:
        cart[key] -= 1
        if cart[key] <=0:
            del cart[key]

    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/remove-cart/<int:product2_id>", methods=["POST"])
def remove_cart(product2_id):
    cart = session.get("cart", {})
    key = str(product2_id)

    if key in cart:
        del cart[key]

    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    cart_data2 = session.get("cart", {})

    cart_products2 = []
    for product2 in get_all_products():
        key = str(product2["id"]) 
        if key in cart_data2:
            quantity2 = cart_data2[key]
            subtotal2 = product2["price"] * quantity2

            cart_products2.append({
                "id": product2["id"],
                "name": product2["name"],
                "price": product2["price"],
                "quantity": quantity2,
                "subtotal": subtotal2,
                "stock": product2["stock"]
            })

    total_price2 = 0
    total_quantity2 = 0
    for product2 in cart_products2:
        total_price2 += product2["subtotal"]
        total_quantity2 += product2["quantity"]
        
    return render_template("cart.html", cart_products2=cart_products2, total_price2=total_price2,total_quantity2=total_quantity2)

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    execute_query(cursor,"SELECT * FROM users2 WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return redirect(url_for("login"))

    execute_query(cursor,"SELECT * FROM orders2 WHERE user_id = ? ORDER BY id DESC", (session["user_id"],))
    user_orders2 = cursor.fetchall()

    orders_with_items = []
    for order2 in user_orders2:
        execute_query(cursor,"SELECT * FROM order_items2 WHERE order_id = ?", (order2["id"],))
        items2 = cursor.fetchall()
        orders_with_items.append({
            "id": order2["id"],
            "address": order2["address"],
            "total": order2["total"],
            "status": order2["status"],
            "products": items2
        })

    conn.close()

    return render_template("profile.html", user=user, orders2=orders_with_items)

DEBUG_MODE = os.getenv("FLASK_DEBUG", "0") == "1"

if __name__ == "__main__":
    app.run(debug=DEBUG_MODE)