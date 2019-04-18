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
    try:
        username = request.form.get('username')
        pw = request.form.get('password')
        adminPW = request.form.get('adminPW')
        hashed = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
        # FOR NOW: global admin password == 'admin'
        isAdmin = 0
        if adminPW == 'admin':
            isAdmin = 1
        # query the database to see if there is a matching username and password
        tryToLoginDict = courseBrowser.getUser(conn, username, hashed, isAdmin)
        # valid login and pw
        if tryToLoginDict['response'] == 0:
            session['uid'] = tryToLoginDict['uid']
            render_template("search.html", loginbanner = "Logged in as " + tryToLoginDict["name"])
        # incorrect pw entered
        if tryToLoginDict['response'] == 1:
            flash("You have entered a valid username, but an incorrect password. Please try again.")
            render_template("index.html")
        # creating a new user with entered username and pw
        else:
            session['uid'] = tryToLoginDict['uid']
            render_template("search.html", loginbanner = "New user created. Logged in as " + tryToLoginDict["name"])
    except Exception as err:
        flash('form submission error '+str(err))
        return redirect(url_for('homePage'))
        
    # if the username exists in the database but the password is wrong,
    # flash a warning to the user and redirect
        
    # if the username is not in the database, then 
    # update the database by creating a new user with that login and password information
    
    
    
    return render_template('index.html') 
   
@app.route('/createAccount', methods=['POST'])
def createAccount():
    return render_template('index.html')
    

@app.route('/search', methods=['POST'])
def search():
    # search for courses
    # redirects to post.html
    conn = courseBrowser.getConn('c9')
    if (request.method == 'POST'):
        searchterm = request.form.get('searchterm')
    courses = courseBrowser.getSearchResults(conn, searchterm)
    return render_template('search.html', courses = courses)
    
@app.route('/createPost/', methods=['POST'])
def createPost():
    if (request.method == 'POST'):
        session['uid'] = request.form['uid']
    return redirect(request.referrer)

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
    app.run('0.0.0.0', 8082)
