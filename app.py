from flask import (Flask, url_for, render_template, request, redirect, flash, session, json, jsonify)
import MySQLdb
import math, random, string
import courseBrowser
import os
import bcrypt

''' Create a connection to the c9 database. '''
conn = MySQLdb.connect(host='localhost',
                        user='ubuntu',
                        passwd='',
                        db='c9')
curs = conn.cursor()
app = Flask(__name__)

app.secret_key = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])

''' Route for a home page and renders the home template.'''
@app.route('/')
def homePage():
    return render_template('index.html')
 
@app.route('/login', methods=['POST'])
def login():
    """Function for the main log in page."""
    #create the login -- if the username is already taken, then search the database
    #for a matching username and hashed password
    conn = courseBrowser.getConn('c9')
    username = request.form.get('username')
    pw = request.form.get('password')
    adminPW = request.form.get('adminPW')
    # FOR NOW: global admin password == 'admin'
    isAdmin = "0"
    if adminPW == 'admin':
        isAdmin = "1"
    # query the database to see if there is a matching username and password
    if username == "" or pw == "":
        flash("You have entered an illegal username or password. Please try again.")
        return render_template('index.html')
    tryToLoginDict = courseBrowser.getUser(conn, username, pw, isAdmin)
    # valid login and pw
    if tryToLoginDict['response'] == 0:
        session['uid'] = tryToLoginDict['uid']
        return render_template('search.html', loginbanner = "Logged in as " + str(tryToLoginDict['name']))
    # incorrect pw entered
    # if the username exists in the database but the password is wrong,
    # flash a warning to the user and redirect
    if tryToLoginDict['response'] == 1:
        flash("You have entered a valid username, but an incorrect password. Please try again.")
        return render_template('index.html')
    # if the username is not in the database, then 
    # update the database by creating a new user with that login and password information
    # creating a new user with entered username and pw
    else:
        session['uid'] = tryToLoginDict['uid']
        return render_template('search.html', loginbanner = "New user created. Logged in as " + str(tryToLoginDict["name"]))
    
    return redirect(url_for('homePage'))
   
@app.route('/createAccount', methods=['POST'])
def createAccount():
    """NOT YET IMPLEMENTED"""
    return render_template('index.html')

@app.route('/search', methods=['GET','POST'])
def search():
    """Function for the search bar in the webpage. Displays results
    similar to the input that user typed into the search bar."""
    # connect to database
    conn = courseBrowser.getConn('c9')
    
    # grab the arguments
    if (request.method == 'POST'):
        searchterm = request.form.get('searchterm')
    else:
        searchterm = request.args.get('searchterm')
    
    # changing the searchterm to be an empty string just in case the result
    # turns out to be None --could probably be improved
    if searchterm is None:
        searchterm = ""
    
    # get the results 
    courses = courseBrowser.getSearchResults(conn, searchterm)
    return render_template('search.html', courses = courses)
    
@app.route('/createPost/<cid>', methods=['GET', 'POST'])
def createPost(cid):
    """Function that redirects to the review page and allows users to create a 
    review for a particular course"""
    #courseAndSemester formatted like this: ECON102-F17
    
    # connect to database 
    conn = courseBrowser.getConn('c9')
    
    # print("course: " + course)
    # print("semester: " + semester)
    #return redirect(request.referrer)
    uid = session.get('uid', False)
    if not uid:
        flash("Sorry, you have to log in before writing a review.")
        return redirect(url_for('homePage'))
    else:
        # get information about particular course
        courseInfo = courseBrowser.getInfoAboutCourse(conn, cid)
        return render_template('post.html', course = courseInfo)
    
@app.route('/insertCourse', methods = ["POST"])
def insertCourse():
    """Inserts a new course into the database and displays it on webpage"""
    conn = courseBrowser.getConn('c9')
    
    # print("session")
    # print(session['uid']) ask scott for help
    uid = session.get('uid', False)
    
    # ensure that user is log in before they add a course
    if not uid:
        flash("Sorry, you have to log in first before adding a course.")
        return redirect(url_for('homePage'))
    else:
        # grab name and semester from form
        name = request.form.get("newcoursename")
        semester = request.form.get("newsemester")
        courseBrowser.insertCourse(conn, name, semester)
        flash("Course added!")
        return redirect(url_for("search"))
      
@app.route('/rateCourse/', methods=['POST'])   
def rateCourse():
    """rate a selected course and update average rating and hours"""
    if 'uid' in session:
        conn = courseBrowser.getConn('c9')
        uid = session['uid']
        cid = request.form.get('cid')
        rating = request.form.get('stars')
        hours = request.form.get('fname')
        comments = request.form.get('comment')
        if courseBrowser.rate_course(conn, uid, cid, rating, hours, comments):
            # print out new average ratings and hours
            avg_rating = courseBrowser.compute_avgrating(conn, cid)
            avg_hours = courseBrowser.compute_avghours(conn, cid)
            
            # update average ratings and hours
            courseBrowser.update_avgrating(conn, cid)
            courseBrowser.update_avghours(conn, cid)
            flash('The new average rating is {} and the new average hours are {}.'.format(avg_rating, avg_hours))
        else:
            flash("Error")
    else:
        flash('You need to login!')
    return redirect(request.referrer) 
    
#we need a main init function
if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0', 8080)
