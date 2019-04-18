from flask import (Flask, url_for, render_template, request, redirect, flash, session, json, jsonify)
import MySQLdb
import math, random, string
import courseBrowser

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
    
@app.route('/createAccount', methods=['POST'])
def createAccount():
    return render_template('index.html')
    
@app.route('/login', methods=['POST'])
def login():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def searchInput():
    # search for courses
    # return redirect(url_for('movieKeywordPage', keyword=keyword))
    return render_template('index.html')
    
@app.route('/createPost', methods=['POST'])
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
