from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.secret_key = "secretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)


# ---------------------
# DATABASE MODELS
# ---------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float)
    category = db.Column(db.String(50))
    user_id = db.Column(db.Integer)


# ---------------------
# HOME
# ---------------------

@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/register")


# ---------------------
# REGISTER
# ---------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# ---------------------
# LOGIN
# ---------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect("/dashboard")

    return render_template("login.html")


# ---------------------
# DASHBOARD
# ---------------------

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        description = request.form["description"]
        amount = float(request.form["amount"])
        category = request.form["category"]

        t = Transaction(
            description=description,
            amount=amount,
            category=category,
            user_id=session["user_id"]
        )

        db.session.add(t)
        db.session.commit()

        return redirect("/dashboard")

    transactions = Transaction.query.filter_by(user_id=session["user_id"]).all()

    total_income = sum(t.amount for t in transactions if t.category == "income")
    total_expense = sum(t.amount for t in transactions if t.category == "expense")
    balance = total_income - total_expense

    return render_template(
        "dashboard.html",
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )


# ---------------------
# DELETE TRANSACTION
# ---------------------

@app.route("/delete/<int:id>")
def delete(id):

    t = Transaction.query.get(id)

    db.session.delete(t)
    db.session.commit()

    return redirect("/dashboard")


# ---------------------
# LOGOUT
# ---------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------------
# CURRENCY CONVERTER
# ---------------------

@app.route("/converter", methods=["GET", "POST"])
def converter():

    converted_amount = None
    rate = None

    if request.method == "POST":

        amount = float(request.form["amount"])
        from_currency = request.form["from_currency"]
        to_currency = request.form["to_currency"]

        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url).json()

        rate = response["rates"][to_currency]
        converted_amount = round(amount * rate, 2)

    return render_template(
        "converter.html",
        converted_amount=converted_amount,
        rate=rate
    )


# ---------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)