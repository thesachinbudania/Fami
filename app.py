from flask import Flask, request, render_template, redirect, session, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from datetime import datetime
import calendar

# setting global variables for the required things
familyMembers = 0
familyNameUq = ""
memberNo = 0

# initializing the app
app = Flask(__name__)

# setting the security key for uses in sessions and cookies
app.secret_key = "Tattiiykk"

# initalizing the database
db = SQL("sqlite:///fami.db")


# the root page which return the home page if the user never logged in or the dashboard by using cookies
@app.route("/")
def main():
    if request.method == "GET":
        # accessing required data from the cookies
        user = request.cookies.get('user')
        hash = request.cookies.get('hash')
        # ensuring the cookies return a value if not then returning the home page template
        if not user or not hash:
            return render_template("home.html")
        # else matching the data in the cookies with the data in the database
        else:
            data = db.execute("SELECT hash,id FROM account_info WHERE name = ?", user)
            # trying to access the hash of the resultant data
            try:
                hashData = data[0]['hash']
            # if there is an indexerror i.e. the database querie didn't returned a value then renedering home page template
            except IndexError:
                return render_template("home.html")
            # matching the hash in the cookie with the hash in the database
            if hashData != hash:
                return render_template("home.html")
            else:
                # storing the id in the session for future references
                id = data[0]['id']
                session['id'] = id
                return redirect("/dashboard")


@app.route("/signup", methods = ["Post", "GET"])
def signup():
    # accessing all the globally declared variables and assigning values to the one's needed in other functions
    global familyNameUq
    global familyMembers
    global memberNo
    # returning the signup page if request method is get
    if request.method == "GET":
        return render_template("signup.html")
    # othewise storing the values in the database
    else:
        # accesssing values from the form
        familyNameUq = request.form.get("familyNameUq")
        familyMembers = request.form.get("familyMembers")
        familyNN = request.form.get("familyNN")
        password = request.form.get("password")
        # trying to select the familyNameUq from the database and if it exists i.e. we don't get an error reprompting the user for the info
        try:
            x = db.execute("SELECT * FROM account_info WHERE name = ?", familyNameUq)[0]
            return render_template("signup.html", error="Family Name taken choose another")
        # if we get an error in there i.e. the family name doesn't exists in the database adding the values to the database
        except IndexError:
            # generating a password hash for safety purposes 
            hash = generate_password_hash(password)
            # inserting the values user provided in the database
            db.execute("INSERT INTO account_info (name, nick_name, hash) VALUES (?, ?, ?)", familyNameUq, familyNN, hash)
         # initializing the memberNo value to show the user which memebers info to be entered in the form on familyRegistration
        memberNo = 1
        return render_template("familyRegistration.html", memberNo = memberNo)


# the family members registration page
@app.route("/familyRegistration", methods = ["POST", "GET"])
def familyRegistration():
    # accessing the values of the globally declared variables
    global familyNameUq
    global familyMembers
    global memberNo
    # submitting the values user provided for a family member
    if request.method == "POST":
        # accessing the values of the form
        memberName = request.form.get("memberName")
        contact = request.form.get("contact")
        email = request.form.get("email")
        # accessing the family_id of the user from the global variable
        family_id = db.execute("SELECT id FROM account_info WHERE name = ?", familyNameUq)[0]['id']
        # now inserting the values the user provided for a member with the family_id
        db.execute("INSERT INTO members (family_id, name, contact, email) VALUES (?, ?, ?, ?)", family_id, memberName, contact, email)
        # now we have registered a family member so subtracting one from the no. of members to be registered
        familyMembers = int(familyMembers)
        familyMembers -= 1
        # adding one to the no. of the member we need to register now
        memberNo += 1
        # if remaining members to register is greater than zero than again showing the familyRegistration form with the updated member no to be registered
        if familyMembers > 0:
            return render_template("familyRegistration.html", memberNo = memberNo)
        # if remaining family members is not greater than zero i.e. all the specified members in the family are registered then showing the login page
        else :
            return render_template("login.html")


# the login page
@app.route("/login", methods = ["POST", "GET"])
def login():
    # rendering the login page if request method is get
    if request.method == "GET":
        return render_template("login.html")
    # otherwise loggin the user in 
    elif request.method == "POST":
        # accessing the values of the family name and password provided by the user
        user = request.form.get("familyNameUq")
        password = request.form.get("password")
        # accessing the hash and id from the database with the given username
        data = db.execute("SELECT hash,id FROM account_info WHERE name = ?", user)
        # trying to access the hash of the returned data by the sqlite3 query
        try :
            hash = data[0]['hash']
        # if an index error happens i.e. there's no data of the user in the records then returning the login page again with the error message
        except IndexError:
            return render_template("login.html", error="Sorry but no records with the given family name found")
        # if the given password and the database hash are not same then returning the error message
        if check_password_hash(hash, password) == False:
            return render_template("login.html", error="Sorry but your password is incorrect")
        # otherwise logging the user in 
        else:
            # setting a session for the user with the user's id for future reference
            id = data[0]['id']
            session['id'] = id
            # setting up the cookies so that the user don't need to login again
            resp = make_response(redirect("/dashboard"))
            resp.set_cookie('user', value=user)
            resp.set_cookie('hash', value=hash)
            # returning the dashboard template
            return resp

@app.route("/dashboard/<clicked_name>", methods=["GET"])
@app.route("/dashboard")
def dashboard(clicked_name=None):
    if request.method == "GET":
        if clicked_name:
            resp = make_response(redirect("/dashboard"))
            resp.set_cookie('name', value=clicked_name)
            return resp
        elif not request.cookies.get('name'):
            data = db.execute("SELECT name FROM members WHERE family_id = ?", session['id'])
            return render_template("whoYouAre.html", names=data)
        else:
            name = request.cookies.get('name').capitalize()
            current_month = datetime.now().month
            current_day = datetime.now().day
            familyName = db.execute("SELECT name FROM account_info WHERE id = ?", session['id'])[0]['name']
            if current_day < 24:
                checkUpto = current_day + 7
                dataUpcoming = db.execute("SELECT member_name, task, day, month, hour, minute FROM tasks WHERE family_name = ? AND month = ? AND day > ? AND day < ?", familyName, calendar.month_name[current_month], current_day, checkUpto)
                dataNames = db.execute("SELECT name FROM members WHERE family_id = ?", session['id'])
                return render_template("dashboard.html", name=checkUpto, dataNames=dataNames, dataUpcoming=dataUpcoming)
            else:
                checkUpto = 7 - (31 - current_day)
                dataUpcoming = db.execute("SELECT member_name, task, day, month, hour, minute FROM tasks WHERE family_name = ? AND ((month = ? AND day > ? AND day < 31) OR (month = ? AND day < ?))", familyName, calendar.month_name[current_month], current_day, calendar.month_name[current_month + 1], checkUpto)
                dataNames = db.execute("SELECT name FROM members WHERE family_id = ?", session['id'])
                return render_template("dashboard.html", name=name, dataNames=dataNames, dataUpcoming=dataUpcoming)
        

@app.route("/new", methods=["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template("add.html")
    else:
        name = request.cookies.get('name')
        family_name = request.cookies.get('user')
        task = request.form.get('toBeRemembered')
        month = request.form.get('month')
        day = request.form.get('day')
        hour = request.form.get('hour')
        minute = request.form.get('minute')
        db.execute("INSERT INTO tasks (family_name, member_name, task, month, day, hour, minute) VALUES (?, ?, ?, ?, ?, ?, ?)", family_name, name, task, month, day, hour, minute)
        return redirect("/dashboard")


@app.route("/see/<clicked_name>" , methods=['GET'])
def see(clicked_name):
    family_name = request.cookies.get('user')
    data = db.execute("SELECT task, month, day, hour, minute FROM tasks WHERE family_name = ? AND member_name = ?", family_name, clicked_name)
    return render_template("view.html", data=data, name=clicked_name)


if __name__ == '__main__':
    app.run(debug = True)