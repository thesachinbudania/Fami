from flask import Flask, request, render_template, redirect

app = Flask(__name__)

@app.route("/")
def main():
    if request.method == "GET":
        return render_template("home.html")


@app.route("/signup")
def signup():
    if request.method == "GET":
        return render_template("signup.html")