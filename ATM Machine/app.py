from flask import Flask, render_template, request, redirect, session, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = "atmsecret"

# Dummy user database
users = {
    "12345678": {
        "pin": "1234",
        "balance": 15000,
        "transactions": []
    }
}

# -------------------- LOGIN PAGE --------------------

@app.route("/")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    card = request.form["card"]
    pin = request.form["pin"]

    if card in users and users[card]["pin"] == pin:
        session["card"] = card
        return redirect(url_for("dashboard"))
    else:
        return "Invalid Card Number or PIN"


# -------------------- DASHBOARD --------------------

@app.route("/dashboard")
def dashboard():
    if "card" not in session:
        return redirect(url_for("login_page"))

    user = users[session["card"]]
    return render_template("dashboard.html", balance=user["balance"])


# -------------------- DEPOSIT --------------------

@app.route("/deposit", methods=["POST"])
def deposit():
    if "card" not in session:
        return redirect(url_for("login_page"))

    amount = int(request.form["amount"])
    user = users[session["card"]]

    user["balance"] += amount

    transaction = {
        "type": "Deposit",
        "amount": amount,
        "balance": user["balance"],
        "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }

    user["transactions"].append(transaction)
    session["last_transaction"] = transaction

    return redirect(url_for("transaction_result"))


# -------------------- WITHDRAW --------------------

@app.route("/withdraw", methods=["POST"])
def withdraw():
    if "card" not in session:
        return redirect(url_for("login_page"))

    amount = int(request.form["amount"])
    user = users[session["card"]]

    if amount > user["balance"]:
        return "Insufficient Balance"

    user["balance"] -= amount

    transaction = {
        "type": "Withdraw",
        "amount": amount,
        "balance": user["balance"],
        "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }

    user["transactions"].append(transaction)
    session["last_transaction"] = transaction

    return redirect(url_for("transaction_result"))


# -------------------- TRANSACTION RESULT --------------------

@app.route("/transaction_result")
def transaction_result():
    if "card" not in session:
        return redirect(url_for("login_page"))

    transaction = session.get("last_transaction")

    if not transaction:
        return redirect(url_for("dashboard"))

    return render_template("transaction_result.html", t=transaction)


# -------------------- FULL HISTORY --------------------

@app.route("/history")
def history():
    if "card" not in session:
        return redirect(url_for("login_page"))

    user = users[session["card"]]
    return render_template("history.html", transactions=user["transactions"])


# -------------------- CHANGE PIN --------------------

@app.route("/change_pin", methods=["POST"])
def change_pin():
    if "card" not in session:
        return redirect(url_for("login_page"))

    old_pin = request.form["old_pin"]
    new_pin = request.form["new_pin"]

    user = users[session["card"]]

    if old_pin == user["pin"]:
        user["pin"] = new_pin
        return redirect(url_for("dashboard"))
    else:
        return "Wrong Old PIN"


# -------------------- LOGOUT --------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# -------------------- RUN APP --------------------

if __name__ == "__main__":
    app.run(debug=True)
