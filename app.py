from flask import Flask, request, render_template, redirect, session, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from datetime import datetime, timedelta
import calendar
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
import pytz


# setting the variable for scheduling the notifications
notificationSchedule = BackgroundScheduler()


# setting the function to check if it's time to send a notification
def noticationChecker():
    current_day = datetime.now(pytz.timezone('Asia/Kolkata')).day
    current_month = calendar.month_name[datetime.now(pytz.timezone('Asia/Kolkata')).month]
    current_hour = datetime.now(pytz.timezone('Asia/Kolkata')).hour
    current_minute = datetime.now(pytz.timezone('Asia/Kolkata')).minute
    scheduled = db.execute("SELECT family_name, member_name, task FROM tasks WHERE month = ? AND day = ? AND hour = ? AND minute = ?", current_month, current_day, current_hour, current_minute + 1)
    if scheduled:
        print("scheduled")
        s = smtplib.SMTP('smtp.gmail.com' , 587)
        s.starttls()
        s.login('withlovefami@gmail.com', 'ihntnsbxepiabadu')
        for data in scheduled:    
            headers = "From: Fami\r\nSubject: Your family members need to be reminded"
            message = f"\nHello there\nA general reminder that {data['member_name']} is to be reminded of {data['task']}\n\n\n\n\nNote: You are recieving this email because someone if not you added your email address as an email address of their family members knowingly or unknowingly\n\n\n\n\\n\n\n\nWith \u2764 From Fami"
            email_body = headers + message
            email_body = email_body.encode('utf-8')
            emails = db.execute("SELECT email FROM members JOIN account_info ON account_info.id = members.family_id WHERE account_info.name = ?", data['family_name'])
            reciptents = []
            for c in emails:
                print(c['email'] + " Email sent")
                reciptents.append(c['email'])
            s.sendmail('Fami', reciptents, email_body)
        return
    else:
        return True


# adding the job to the schedular to check in a given time fram for notifications
notificationSchedule.add_job(noticationChecker, 'interval', minutes=1)
notificationSchedule.start()

# starting the schedular
# notificationSchedule.start()


# setting global variables for the required things
familyMembers = 0
familyNameUq = ""
memberNo = 0
nameN = ""

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
            resp.set_cookie('user', value=user, expires=datetime.now() + timedelta(days=30))
            resp.set_cookie('hash', value=hash, expires=datetime.now() + timedelta(days=30))
            # returning the dashboard template
            return resp

@app.route("/dashboard/<clicked_name>", methods=["GET"])
@app.route("/dashboard")
def dashboard(clicked_name=None):
    if request.method == "GET":
        if clicked_name:
            resp = make_response(redirect("/dashboard"))
            resp.set_cookie('name', value=clicked_name, expires=datetime.now() + timedelta(days=30))
            return resp
        elif not request.cookies.get('name'):
            data = db.execute("SELECT name FROM members WHERE family_id = ?", session['id'])
            return render_template("whoYouAre.html", names=data)
        else:
            name = request.cookies.get('name').capitalize()
            current_month = datetime.now(pytz.timezone('Asia/Kolkata')).month
            current_day = datetime.now(pytz.timezone('Asia/Kolkata')).day
            familyName = db.execute("SELECT name FROM account_info WHERE id = ?", session['id'])[0]['name']
            if current_day < 24:
                checkUpto = current_day + 7
                dataUpcoming = db.execute("SELECT member_name, task, day, month, hour, minute FROM tasks WHERE family_name = ? AND month = ? AND day > ? AND day < ?", familyName, calendar.month_name[current_month], current_day - 1, checkUpto + 1)
                dataNames = db.execute("SELECT name FROM members WHERE family_id = ?", session['id'])
                return render_template("dashboard.html", name=name, dataNames=dataNames, dataUpcoming=dataUpcoming)
            else:
                checkUpto = 7 - (31 - current_day)
                dataUpcoming = db.execute("SELECT member_name, task, day, month, hour, minute FROM tasks WHERE family_name = ? AND ((month = ? AND day > ? AND day < 32) OR (month = ? AND day < ?))", familyName, calendar.month_name[current_month], current_day - 1, calendar.month_name[current_month + 1], checkUpto + 1)
                dataNames = db.execute("SELECT name FROM members WHERE family_id = ?", session['id'])
                return render_template("dashboard.html", name=name, dataNames=dataNames, dataUpcoming=dataUpcoming)
        

@app.route("/new", methods=["GET", "POST"])
def add():
    if request.method == "GET":
        name = request.cookies.get('name')
        return render_template("add.html", name=name)
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
    data = db.execute("SELECT task, month, day, hour, minute FROM tasks WHERE family_name = ? AND member_name = ? ", family_name, clicked_name)
    return render_template("view.html", data=data, name=clicked_name)


@app.route("/deleteTask/<task>/<day>/<month>/<source>")
def deleteTask(task, day, month, source):
    name = request.cookies.get('name')
    family_name = request.cookies.get('user') 
    db.execute("DELETE FROM tasks WHERE task = ? AND month = ? AND day = ? AND family_name = ?", task, month, day, family_name)
    if source == 'dashboard':
      return redirect('/dashboard')
    elif source == 'viewTask':  
      return redirect(f'/see/{name}')
    else :
      return None


@app.route('/docs')
def docs():
    return render_template('docs.html')


@app.route('/manage')
def manage():
    return render_template('manage.html')

@app.route('/changeMembers', methods = ['GET', 'POST'])
@app.route('/changeMembers/<option>/<member>', methods = ['GET', 'POST'])
@app.route('/changeMembers/<option>', methods = ['GET', 'POST'])
def changeMembers(option=None, member=None):
    names = db.execute("SELECT name FROM members WHERE family_id = ?", session['id'])
    if request.method == 'GET':
        if not option:
            return render_template('changeMembers.html', names=names)
        elif option == 'remove':
            if not member:
                return render_template('removeMember.html', names=names)
            elif member:
                db.execute('DELETE FROM members WHERE family_id = ? AND name = ?', session['id'], member)
                db.execute("DELETE FROM tasks WHERE family_name = ? AND member_name = ?", request.cookies.get('user'), member)
                return render_template('removeMember.html', names=names)
        elif option == 'add':
            if request.method == 'GET':
                return render_template('addMember.html')
    else:
        name = request.form.get('name')
        phoneNo = request.form.get('phoneNo')
        email = request.form.get('email')
        db.execute('INSERT INTO members(family_id, name, contact, email) VALUES (?, ?, ?, ?)', session['id'], name, phoneNo, email)
        return render_template('addMember.html', message='Member added successfully')


@app.route('/changeDetails', methods=['GET', 'POST'])
@app.route('/changeDetails/<name>', methods=['GET', 'POST'])
def changeDetails(name=None):
    global nameN
    if request.method == 'GET':
        if not name:
            names = db.execute("SELECT name FROM members WHERE family_id = ?", session['id'])
            return render_template('changeDetails.html', members=names)
        else:
            data = db.execute('SELECT name, contact, email FROM members WHERE family_id = ? AND name = ?', session['id'], name)
            nameN = data[0]['name']
            return render_template('selectDetails.html', name=nameN, phone=data[0]['contact'], email=data[0]['email'])
    else:
        newName = request.form.get('newName')
        newContact = request.form.get('newContact')
        newEmail = request.form.get('newEmail')
        db.execute('UPDATE members SET name = ?, email = ?, contact = ? WHERE name = ? AND family_id = ?', newName, newEmail, newContact, nameN, session['id'])
        return render_template('selectDetails.html', message="Details updated successfully")


@app.route('/resetPassword', methods=['GET', 'POST'])
def resetPassword():
    if request.method == 'GET':
        return render_template('resetPassword.html')
    else:
        currentPassword = request.form.get('currentPassword')
        newPassword = request.form.get('newPassword')
        originalHash = db.execute("SELECT hash FROM account_info WHERE id = ?", session['id'])
        if check_password_hash(originalHash[0]['hash'], currentPassword) == False:
            return render_template('resetPassword.html', message="Please enter correct current password")
        else:
            db.execute('UPDATE account_info SET hash = ? WHERE id = ?', generate_password_hash(newPassword), session['id'])
            return render_template('resetPassword.html', message="Password updated successfully")


@app.route('/logout')
def logout():
    response = make_response(redirect('/'))
    cookies = request.cookies
    for cookie in cookies:
        response.delete_cookie(cookie)
    return response


@app.route('/deleteAccount', methods=['GET', 'POST'])
def deleteAccount():
    if request.method == "GET":
        return render_template('deleteAccount.html')
    else:
        password = request.form.get('password')
        originalHash = db.execute('SELECT hash FROM account_info WHERE id = ?', session['id'])
        if check_password_hash(originalHash[0]['hash'], password) == False:
            return render_template('deleteAccount.html', info="Wrong Password")
        else:
            try:
                db.execute('DELETE FROM account_info WHERE id = ?', session['id'])
                return redirect('/')
            except:
                return render_template('deleteAccount.html', info='Something went wrong! Please try again')

@app.route('/legendAbhinav')
def legendAbhianv():
    return render_template('analAbhinav.html')


if __name__ == '__main__':
    app.run(debug=False)
