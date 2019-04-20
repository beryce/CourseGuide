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
    #create the login -- if the username is already taken, then search the database
    #for a matching username and hashed password
    username = request.form.get('username')
    pw = request.form.get('password')
    adminPW = request.form.get('adminPW')
    # FOR NOW: global admin password == 'admin'
    isAdmin = 0
    if adminPW == 'admin':
        isAdmin = 1
    # query the database to see if there is a matching username and password
    tryToLoginDict = courseBrowser.getUser(conn, username, pw, isAdmin)
    # valid login and pw
    if tryToLoginDict['response'] == 0:
        print("in part 1")
        session['uid'] = tryToLoginDict['uid']
        return render_template('search.html', loginbanner = "Logged in as " + str(tryToLoginDict['name']))
    # incorrect pw entered
    # if the username exists in the database but the password is wrong,
    # flash a warning to the user and redirect
    if tryToLoginDict['response'] == 1:
        print("in part 2")
        flash("You have entered a valid username, but an incorrect password. Please try again.")
        return render_template('index.html')
    # if the username is not in the database, then 
    # update the database by creating a new user with that login and password information
    # creating a new user with entered username and pw
    else:
        print("in part 3")
        print(tryToLoginDict)
        session['uid'] = tryToLoginDict['uid']
        return render_template('search.html', loginbanner = "New user created. Logged in as " + str(tryToLoginDict["name"]))
    
    return redirect(url_for('homePage'))
   
@app.route('/createAccount', methods=['POST'])
def createAccount():
    return render_template('index.html')
    

@app.route('/search', methods=['GET','POST'])
def search():
    """Function for the search bar in the webpage. Displays results
    similar to the input that user typed into the search bar."""
    conn = courseBrowser.getConn('c9')
    if (request.method == 'POST'):
        searchterm = request.form.get('searchterm')
    else:
        searchterm = request.args.get('searchterm')
    
    # changing the searchterm to be an empty string just in case the result
    # turns out to be None --could probably be improved
    if searchterm is None:
        searchterm = ""
        
    courses = courseBrowser.getSearchResults(conn, searchterm)
    return render_template('search.html', courses = courses)
    
@app.route('/createPost/<cid>', methods=['GET', 'POST'])
def createPost(cid):
    #courseAndSemester formatted like this: ECON102-F17
    conn = courseBrowser.getConn('c9')
    if (request.method == 'POST'):
        session['uid'] = request.form['uid']
    # print("course: " + course)
    # print("semester: " + semester)
    #return redirect(request.referrer)
    courseInfo = courseBrowser.getInfoAboutCourse(conn, cid)
    return render_template('post.html', course = courseInfo)

#necessary?  
@app.route('/updatePost', methods=['POST'])
def updatePost():
    if (request.method == 'POST'):
        session['uid'] = request.form['uid']
    return redirect(request.referrer) 
#necessary?     
@app.route('/deletePost', methods=['POST'])
def deletePost():
    if (request.method == 'POST'):
        session['uid'] = request.form['uid']
    return redirect(request.referrer)
    
@app.route('/insertCourse')
def insertCourse():
    return redirect(request.referrer)   
    
#we need a main init function
if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0', 8081)
