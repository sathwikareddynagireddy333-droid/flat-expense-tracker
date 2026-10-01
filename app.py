from flask import Flask, render_template, request, redirect, session
import mysql.connector
from dotenv import load_dotenv
from datetime import date, timedelta
import os

load_dotenv()

PRIVATE_ACCESS_PIN = os.getenv("PRIVATE_ACCESS_PIN")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.permanent_session_lifetime = timedelta(days=365)

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
@app.route("/", methods=["GET", "POST"])
def home():

    if not session.get("logged_in"):
        return redirect("/login")

    if request.method == "POST":

  
        name = request.form["name"]
        item = request.form["item"]
        amount = request.form["amount"]
        expense_date = request.form["date"]

        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO expenses (name, item, amount, date, time)
            VALUES (%s, %s, %s, %s, CURTIME())
            """,
            (name, item, amount, expense_date)
        )

        db.commit()
        cursor.close()

        return redirect("/")

    # Get all expenses for Expense History
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, name, item, amount, date, time
        FROM expenses
        ORDER BY date DESC, time DESC
        """
    )

    expenses = cursor.fetchall()

    # Calculate current month's spending
    current_month = date.today().strftime("%Y-%m")

    cursor.execute(
        """
        SELECT name, SUM(amount) AS total
        FROM expenses
        WHERE DATE_FORMAT(date, '%Y-%m') = %s
        GROUP BY name
        """,
        (current_month,)
    )

    spending_data = cursor.fetchall()

    cursor.close()

    # Start everyone at zero
    spending = {
        "Deepa": 0,
        "Vennela": 0,
        "Sathwika": 0
    }

    # Put actual spending into the correct person
    for row in spending_data:
        spending[row["name"]] = float(row["total"])

    # Fixed monthly rent
    rent = 20000

    # Total expenses + rent
    total_spending = sum(spending.values())
    total_monthly_cost = total_spending + rent

    # Equal share for 3 people
    equal_share = total_monthly_cost / 3

    # Rent each person needs to pay
    rent_to_pay = {}

    for name in spending:
        rent_to_pay[name] = equal_share - spending[name]

    summary = []

    for name in ["Deepa", "Vennela", "Sathwika"]:
        summary.append({
            "name": name,
            "spent": spending[name],
            "rent_to_pay": rent_to_pay[name]
        })

    return render_template(
        "index.html",
        expenses=expenses,
        summary=summary
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        entered_pin = request.form["pin"]

        if entered_pin == PRIVATE_ACCESS_PIN:
            session.permanent = True
            session["logged_in"] = True
            return redirect("/")

        return render_template(
            "login.html",
            error="Incorrect PIN. Please try again."
        )

    return render_template("login.html")


if __name__ == "__main__":
    
    app.run(debug=False)