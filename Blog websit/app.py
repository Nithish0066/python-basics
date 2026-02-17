from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

login_manager = LoginManager()
login_manager.init_app(app)

# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect("blog.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            category_id INTEGER,
            author TEXT,
            date TEXT,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- USER CLASS ----------------

class User(UserMixin):
    def __init__(self, id, username, password, role):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user["id"], user["username"], user["password"], user["role"])
    return None

# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("select.html")

# ---------------- ADMIN LOGIN ----------------

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND role='admin'",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            login_user(User(user["id"], user["username"], user["password"], user["role"]))
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid Admin Credentials")

    return render_template("admin_login.html")

# ---------------- USER LOGIN ----------------

@app.route("/user-login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND role='user'",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            login_user(User(user["id"], user["username"], user["password"], user["role"]))
            return redirect(url_for("user_dashboard"))
        else:
            flash("Invalid User Credentials")

    return render_template("user_login.html")

# ---------------- USER REGISTER ----------------

@app.route("/user-register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, "user")
            )
            conn.commit()
            flash("Registered Successfully")
            return redirect(url_for("user_login"))
        except:
            flash("Username already exists")
        finally:
            conn.close()

    return render_template("user_register.html")

# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin-dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    conn = get_db()

    posts = conn.execute("""
        SELECT posts.id,
               posts.title,
               posts.content,
               posts.author,
               posts.date,
               categories.name as category_name
        FROM posts
        LEFT JOIN categories
        ON posts.category_id = categories.id
        ORDER BY posts.id DESC
    """).fetchall()

    categories = conn.execute("SELECT * FROM categories").fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        posts=posts,
        categories=categories
    )


# ---------------- CREATE POST ----------------

@app.route("/create-post", methods=["GET", "POST"])
@login_required
def create_post():

    if current_user.role != "admin":
        return redirect(url_for("home"))

    conn = get_db()
    categories = conn.execute("SELECT * FROM categories").fetchall()

    if request.method == "POST":

        author_name = request.form["author"]

        conn.execute("""
            INSERT INTO posts (title, content, category_id, author, date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.form["title"],
            request.form["content"],
            request.form["category"],
            author_name,
            datetime.now().strftime("%Y-%m-%d")
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("admin_dashboard"))

    conn.close()
    return render_template("create_post.html", categories=categories)

# ---------------- ADD CATEGORY ----------------

@app.route("/add-category", methods=["POST"])
@login_required
def add_category():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    conn = get_db()
    conn.execute("INSERT INTO categories (name) VALUES (?)",
                 (request.form["name"],))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))

# ---------------- EDIT POST ----------------

@app.route("/edit-post/<int:id>", methods=["GET", "POST"])
@login_required
def edit_post(id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    conn = get_db()

    if request.method == "POST":
        conn.execute(
            "UPDATE posts SET title=?, content=?, category_id=? WHERE id=?",
            (
                request.form["title"],
                request.form["content"],
                request.form["category"],
                id
            )
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_dashboard"))

    post = conn.execute("SELECT * FROM posts WHERE id=?", (id,)).fetchone()
    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()

    return render_template("edit_post.html", post=post, categories=categories)

# ---------------- DELETE POST ----------------

@app.route("/delete-post/<int:id>")
@login_required
def delete_post(id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))

# ---------------- USER DASHBOARD ----------------

@app.route("/user-dashboard")
@login_required
def user_dashboard():
    if current_user.role != "user":
        return redirect(url_for("home"))

    category_id = request.args.get("category")

    conn = get_db()

    if category_id:
        posts = conn.execute("""
            SELECT posts.*, categories.name as category_name
            FROM posts
            LEFT JOIN categories ON posts.category_id = categories.id
            WHERE posts.category_id = ?
        """, (category_id,)).fetchall()
    else:
        posts = conn.execute("""
            SELECT posts.*, categories.name as category_name
            FROM posts
            LEFT JOIN categories ON posts.category_id = categories.id
        """).fetchall()

    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()

    return render_template(
        "user_dashboard.html",
        posts=posts,
        categories=categories
    )




# ---------------- VIEW POST ----------------

@app.route("/post/<int:id>")
@login_required
def view_post(id):
    conn = get_db()
    post = conn.execute("""
        SELECT posts.*, categories.name as category_name
        FROM posts
        LEFT JOIN categories ON posts.category_id = categories.id
        WHERE posts.id=?
    """, (id,)).fetchone()
    conn.close()

    return render_template("view_post.html", post=post)

# ---------------- LOGOUT ----------------

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
