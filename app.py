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

@app.route('/addCourse/')
def add_course():
    return render_template('addcourse.html')
 
@app.route('/login', methods=['POST'])
def login():
    """Function for the main log in page."""
    #create the login -- if the username is already taken, then search the database
    #for a matching username and hashed password
    conn = courseBrowser.getConn('c9')
    username = request.form.get('username')
    pw = request.form.get('password')
    adminPW = request.form.get('adminPW')
    
    # course examples displayed after successful login
    dummyCourses = courseBrowser.getSearchResults(conn, "", "", "")
    
    # FOR NOW: global admin password == 'admin'
    isAdmin = "0"
    if adminPW == 'admin': # needs to be stored more securely (this will show up on view source)
    # if admin is not empty password, go look up in bcrypt (bcrypt it and compare it to something you read from a table)
    # another way--have a boolean with each person's username on whether they're the administrator
    # can put this boolean in the session to avoid having to check database
        isAdmin = "1"
    # query the database to see if there is a matching username and password
    if username == "" or pw == "":
        flash("Invalid username/password.")
        return render_template('index.html')
    tryToLoginDict = courseBrowser.getUser(conn, username, pw, isAdmin)
    # valid login and pw
    if tryToLoginDict['response'] == 0:
        session['uid'] = tryToLoginDict['uid']
        return render_template('search.html', loginbanner = "Logged in as " + str(tryToLoginDict['name']), courses=dummyCourses)
    # incorrect pw entered
    # if the username exists in the database but the password is wrong,
    # flash a warning to the user and redirect
    if tryToLoginDict['response'] == 1:
        flash("Invalid username/password.")
        return render_template('index.html')
    # if the username is not in the database, then 
    # update the database by creating a new user with that login and password information
    # creating a new user with entered username and pw
    else:
        session['uid'] = tryToLoginDict['uid']
        return render_template('search.html', loginbanner = "New user created. Logged in as " + str(tryToLoginDict["name"]), courses=dummyCourses)
    
    return redirect(url_for('homePage'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Function for the search bar in the webpage. Displays results
    similar to the input that user typed into the search bar."""
    
    conn = courseBrowser.getConn('c9')
    if request.method == 'POST':
        searchterm = request.form.get('searchterm', "")
        semester = request.form.get('semester_filter', "")
        prof = request.form.get('professor_filter', "")
    else:
        searchterm = request.args.get('searchterm', "")
        semester = request.args.get('semester_filter', "")
        prof = request.form.get('professor_filter', "")
        
    courses = courseBrowser.getSearchResults(conn, searchterm, semester, prof)
    return render_template('search.html', courses=courses)

# I don't think we need this anymore, but I'm keeping this here just in case
# @app.route('/updateSearch', methods=['POST'])
# def update_search():
#     """Function for the filterbar in the webpage. Displays results
#     similar to the input that user typed into the filter bar."""
#     # connect to database
#     conn = courseBrowser.getConn('c9')
    
#     # grab the arguments]
#     semester = request.form.get('semester_filter', "")
#     # get the results 
#     courses = courseBrowser.updateSearch(conn, semester)
#     print("COURSES: ")
#     print(courses)
#     # return redirect(url_for('search', courses = courses))
#     return render_template('search.html', courses = courses)
    
@app.route('/createPost/<cid>', methods=['GET', 'POST'])
def createPost(cid):
    """Function that redirects to the review page and allows users to create a 
    review for a particular course"""
    #courseAndSemester formatted like this: ECON102-F17
    
    # connect to database 
    conn = courseBrowser.getConn('c9')

    uid = session.get('uid', False)
    if not uid:
        flash("Sorry, you have to log in before writing a review.")
        return redirect(url_for('homePage'))
    else:
        # get information about particular course
        courseInfo = courseBrowser.getInfoAboutCourse(conn, cid)
        pastComments = courseBrowser.get_past_comments(conn, cid)
        return render_template('post.html', course = courseInfo, rows = pastComments)
    
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
        name = request.form.get("newcoursename").upper()
        semester = request.form.get("newsemester").upper().encode("utf-8")
        professor = request.form.get("newprofessor").upper()
        if (len(semester) != 3) or (semester[0]!='F' and semester[0]!='S') or (not (semester[1:].isdigit())):
            flash("Invalid semester.")
            redirect(url_for("search"))
        else:
            if courseBrowser.insertCourse(conn, professor, name, semester):
                flash("Course added!")
            else:
                flash("Uh-oh! It looks like this course already exists in our database...")
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
    
# @app.route('/rateCourseAjax/', methods=['POST'])   
# def rateCourseAjax():
#     """rate a selected course and update average rating and hours"""
#     try:
#         if 'uid' in session:
#             conn = courseBrowser.getConn('c9')
#             uid = session['uid']
#             cid = request.form.get('cid')
#             rating = request.form.get('stars')
#             hours = request.form.get('fname')
#             comments = request.form.get('comment')
#             if courseBrowser.rate_course(conn, uid, cid, rating, hours, comments):
#                 # print out new average ratings and hours
#                 avg_rating = courseBrowser.compute_avgrating(conn, cid)
#                 avg_hours = courseBrowser.compute_avghours(conn, cid)
                
#                 # update average ratings and hours
#                 courseBrowser.update_avgrating(conn, cid)
#                 courseBrowser.update_avghours(conn, cid)
#                 return jsonify({"avg_rating": avg_rating, "avg_hours": avg_hours})
#             else:
#                 return jsonify({"avg_rating": "None", "avg_hours": "None"})
#         else:
#             return jsonify({"avg_rating": "None", "avg_hours": "None"})
#     except:
#         return jsonify({"avg_rating": "None", "avg_hours": "None"})
    
    
#we need a main init function
if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0', 8082)
