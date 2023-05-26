from flask import Flask, request, render_template, redirect
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL

app = Flask(__name__)

db = SQL("sqlite:///fami.db")

@app.route("/")
def main():
    if request.method == "GET":
        return render_template("home.html")


@app.route("/signup")
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    else:
        familyNameUq = request.form.get("familyNameUq")
        familyMembers = request.form.get("familyMembers")
        familyNN = request.form.get("familyNN")
        password = request.form.get("password")
        if not db.execute("SELECT * FROM account_info WHERE name = ?", familyNameUq)[0]:
            return render_template("signup.html", error="Family Name taken choose another")
        else:
            hash = generate_password_hash(password)