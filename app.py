from flask import Flask, render_template, request, session, redirect, url_for, flash
import sqlite3, os
import time, datetime
from passlib.hash import sha256_crypt

from util import dbUpdate, all_stories,users

app = Flask(__name__)

app.secret_key = os.urandom(32)

@app.route("/")
def root():
    if 'username' in session:
        #return redirect("/auth")
        return render_template("home.html", username = session['username'])
    #else:
    #return redirect('/auth')
    return render_template("login.html")


@app.route("/auth", methods = ["POST"])
def check():
    DB_FILE="data/logins.db"
    db = sqlite3.connect(DB_FILE) #open if file exists, otherwise create
    c = db.cursor() #facilitate db ops
    usrn = request.form['username']
    passw= request.form['password']
    #print (usrn, passw)
    cmd = """SELECT * FROM info""" #selecting with WHERE may give errors
    threadC = c.execute(cmd).fetchall()

    for entry in threadC:
        if (entry[0] == usrn):
            print(entry[1])
            print(sha256_crypt.hash(passw))
            if sha256_crypt.verify(passw, entry[1]):
                session['username'] = usrn
                #print(session)
                return '''SUCCESS!!\n<a href="/display?story=Frankenstein">view stories</a>\n<a href="/editPage?story=Frankenstein">edit stories</a>'''
            #return "NAY PASSWORD"
            flash("NAY PASSWORD")
            return redirect("/")

    flash("username " + usrn + " not found. please try again")
    db.commit()
    db.close()

    return redirect("/")
    ##return "no such username"

@app.route("/display")#displays one story selected in entirety
def display():
    if 'username' not in session:
        flash("You have been logged out.")
        return redirect("/")
    DB_FILE = "data/stories.db"
    db = sqlite3.connect(DB_FILE) #open if file exists, otherwise create
    c = db.cursor() #facilitate db ops
    nm = request.args.get("story")
    cmd = """SELECT contribution FROM """ + nm
    contributions = c.execute(cmd).fetchall()
    s = nm+"\n"
    for txt in contributions:
        s += txt[0]+" \n"
    db.commit()
    db.close()

    return render_template("viewStory.html", title = nm, content = s)

@app.route("/editPage")#edit stories
def editPage():
    if 'username' not in session:
        flash("You have logged out.")
        return redirect("/")
    DB_FILE = "data/stories.db"
    db = sqlite3.connect(DB_FILE) #open if file exists, otherwise create
    c = db.cursor() #facilitate db ops
    nm = request.args.get("story")
    session["storyname"] = nm
    # don't know how to select last addition
    cmd = """SELECT * FROM """+nm
    lastC =""
    contributions = c.execute(cmd).fetchall()
    lastC = contributions[len(contributions)-1][2]
    db.commit()
    db.close()
    session['storyname']=nm
    return render_template("editStory.html", title = nm, content = lastC)

@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username')
    flash("You have been successfully logged out.")
    return redirect("/")

@app.route('/addStory', methods = ["POST"])
def parse_submission():
    if 'username' not in session:
        flash("You have been logged out.")
        return redirect("/")
    content = request.form["content"]
    stnm = session['storyname']
    test = (len(content)-1)*" "+"a"
    #print (test)
    if content < test:# makes sure content is not empty
        
        flash("<h1>Please add Content.</h1>")#this flash does not show
        
        session.pop('storyname')
        return redirect("/editPage?story="+stnm)
    usern = session['username']
    
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    dbUpdate.addStories(usern, stnm, content)
    session.pop('storyname')
    return render_template('success.html', title = stnm, time = st)


@app.route('/register', methods = ['POST', 'GET'])
def register():
    # if the 'create user' button is pressed, the method is GET
    # loads the page to create a user
    if request.method == 'GET':
        return render_template("createUser.html")

    # if the 'submit' button is pressed, the method is POST
    # sends the information
    else:
        return addUser()

def addUser():
    # takes user-inputted data
    usrn = request.form["username"]
    pass1 = request.form["password1"]
    pass2 = request.form["password2"]

    # should checks be added for empty user/passw
    # users that are already in the system

    # works even if password field is empty
    # first checks if passwords are matching
    if (pass1 == pass2):
        # success stores the boolean from users.py
        # is the user successfully added to the database? (the username is not already taken)
        success = users.addUser(usrn, pass1)

        # if successfully added
        if success:
            # success message
            flash( "User " + usrn + " created. Please log in.")
            # return to the landing site to log in again
            return redirect("/")

        # username was already taken.
        else:
            flash("Username " + usrn+ " is already taken. please try again")
            return redirect("/register")

    # passwords do not match
    flash ("Your passwords do not match. Please reenter your password")
    return redirect ("/register")

if __name__ == "__main__":
    app.debug = True
    app.run()
