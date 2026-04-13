from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secretkey123"

# ----------------------------
# DATABASE SETUP
# ----------------------------
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ----------------------------
# Taxi Class
# ----------------------------
class Taxi:
    def __init__(self, taxi_id):
        self.taxi_id = taxi_id
        self.location = 'A'
        self.free_time = 0
        self.total_earning = 0
        self.trips = []

taxis = [Taxi(i) for i in range(1, 5)]

# ----------------------------
# Fare Calculation
# ----------------------------
def calculate_fare(pickup, drop):
    distance = abs(ord(drop) - ord(pickup)) * 15
    if distance <= 5:
        return 100
    else:
        return 100 + (distance - 5) * 10

# ----------------------------
# Login Page
# ----------------------------
@app.route('/')
def login():
    return render_template("login.html")

# ----------------------------
# Registration Page
# ----------------------------
@app.route('/register')
def register():
    return render_template("register.html")

@app.route('/register_user', methods=['POST'])
def register_user():
    username = request.form['username']
    password = request.form['password']

    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    except:
        return "❌ Username already exists!"

# ----------------------------
# Login
# ----------------------------
@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user'] = username
        return redirect(url_for('home'))
    else:
        return "❌ Invalid Username or Password"

# ----------------------------
# Logout
# ----------------------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ----------------------------
# Dashboard Page
# ----------------------------
@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    from datetime import datetime
    current_time = datetime.now().hour

    total_taxis = len(taxis)
    total_earnings = sum(t.total_earning for t in taxis)
    available = sum(1 for t in taxis if t.free_time <= current_time)
    busy = total_taxis - available

    return render_template(
        "dashboard.html",
        total_taxis=total_taxis,
        total_earnings=total_earnings,
        available=available,
        busy=busy
    )



# ----------------------------
# Booking Page
# ----------------------------
@app.route('/book_page')
def book_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("booking.html")

# ----------------------------
# Handle Booking
# ----------------------------
@app.route('/book', methods=['POST'])
def book():
    if 'user' not in session:
        return redirect(url_for('login'))

    customer_id = request.form['customer_id']
    pickup = request.form['pickup'].upper()
    drop = request.form['drop'].upper()
    pickup_time = int(request.form['pickup_time'])

    available = []

    for taxi in taxis:
        if pickup_time >= taxi.free_time:
            available.append(taxi)

    if not available:
        return render_template("no_taxi.html")

    selected = min(available, key=lambda x: x.total_earning)

    fare = calculate_fare(pickup, drop)
    travel_time = abs(ord(drop) - ord(pickup))
    drop_time = pickup_time + travel_time

    selected.location = drop
    selected.free_time = drop_time
    selected.total_earning += fare
    selected.trips.append(
        (customer_id, pickup, drop, pickup_time, drop_time, fare)
    )

    return render_template(
        "booking_success.html",
        taxi=selected.taxi_id,
        fare=fare,
        drop_time=drop_time
    )

# ----------------------------
# Display Taxi Details
# ----------------------------
@app.route('/display')
def display():
    if 'user' not in session:
        return redirect(url_for('login'))

    current_time = datetime.now().hour

    return render_template(
        "display.html",
        taxis=taxis,
        current_time=current_time
    )

# ----------------------------
# Run App
# ----------------------------
if __name__ == '__main__':
    app.run(debug=True)
