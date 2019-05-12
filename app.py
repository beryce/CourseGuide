from flask import (Flask, url_for, render_template, request, redirect, flash, session, json, jsonify, send_from_directory, Response)
import MySQLdb
import math, random, string
import courseBrowser
import os
import bcrypt
import imghdr
from werkzeug import secure_filename

# ''' Create a connection to the c9 database. '''
# conn = MySQLdb.connect(host='localhost',
#                         user='ubuntu',
#                         passwd='',
#                         db='c9')
# curs = conn.cursor()
app = Flask(__name__)

app.secret_key = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

# app.config['UPLOADS'] = 'uploads'
app.config['MAX_UPLOAD'] = 256000

def getConn(db):
    conn = MySQLdb.connect(host='localhost',user='ubuntu',passwd='',db=db)
    conn.autocommit(True)
    return conn

''' Route for a home page and renders the home template.'''
@app.route('/')
def homePage():
    # conn = getConn('c9')
    return render_template('index.html')
    
# @app.route('/logout/')
# def logout():
#     # conn = getConn('c9')
#     session['isAdmin'] = False
#     session['uid'] = None
#     session['name'] = None
#     return render_template('index.html')

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
    session['isAdmin'] = False
    if adminPW == 'admin': # needs to be stored more securely (this will show up on view source)
    # if admin is not empty password, go look up in bcrypt (bcrypt it and compare it to something you read from a table)
    # another way--have a boolean with each person's username on whether they're the administrator
    # can put this boolean in the session to avoid having to check database
        isAdmin = "1"
        session['isAdmin'] = True
    # query the database to see if there is a matching username and password
    if username == "" or pw == "":
        flash("Invalid username/password.")
        return render_template('index.html')
    tryToLoginDict = courseBrowser.getUser(conn, username, pw, isAdmin)
    # valid login and pw
    if tryToLoginDict['response'] == 0:
        session['uid'] = tryToLoginDict['uid']
        session['name'] = tryToLoginDict['name']
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
        session['username'] = tryToLoginDict['name']
        return render_template('search.html', loginbanner = "New user created. Logged in as " + str(tryToLoginDict['name']), courses=dummyCourses)

    return redirect(url_for('homePage'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Function for the search bar in the webpage. Displays results
    similar to the input that user typed into the search bar."""
    loginbanner = ""
    if 'name' in session:
        loginbanner = "Logged in as " + session['name']
    
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
    return render_template('search.html', courses=courses, loginbanner=loginbanner)
    
@app.route('/createPost/<cid>', methods=['GET', 'POST'])
def createPost(cid):
    """Function that redirects to the review page and allows users to create a 
    review for a particular course"""
    #courseAndSemester formatted like this: ECON102-F17
    
    conn = courseBrowser.getConn('c9')
    uid = session.get('uid', False)
    if not uid:
        flash("Sorry, you have to log in before writing a review.")
        return redirect(url_for('homePage'))
    else:
        # get information about particular course
        courseInfo = courseBrowser.getInfoAboutCourse(conn, cid)
        pastPosts = courseBrowser.get_past_posts(conn, cid)
        loginbanner = "Logged in as " + session['name']
        return render_template('post.html', course = courseInfo, rows = pastPosts, loginbanner=loginbanner)

@app.route('/editPosts/', methods=['GET', 'POST'])
def editPosts():  
    """Show a user's previous posts only after a user has successfully logged in"""
    conn = courseBrowser.getConn('c9')
    uid = session.get('uid', False)
    if not uid:
        return redirect(url_for('homePage'))
    else:
        posts = courseBrowser.getUserPastPosts(conn, uid)
        return render_template('allPosts.html', posts = posts)
    
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
    
    
@app.route('/delete', methods=['GET', 'POST']) 
def delete():
    """ Function allows users can delete their posts. """
    conn = courseBrowser.getConn('c9')
    loginbanner = ""
    if 'uid' in session and session['uid'] is not None:
        uid = session['uid']
        loginbanner="Logged in as " + session['name']
        
        if (request.method == 'POST'):
            print(request.form.getlist('coursePost'))
            deleteList = request.form.getlist('coursePost')
            for cid in deleteList:
                courseBrowser.deletePost(conn, session['uid'], cid)
            postsDict = courseBrowser.getAllPosts(conn, session['uid'])
            flash('Posts successfully deleted.')
            return render_template('delete.html', rows = postsDict, loginbanner="Logged in as " + session['name'])
        
        postsDict = courseBrowser.getAllPosts(conn, uid)
        if postsDict is None:
            flash('You have made 0 posts. You need to create a post first before you can delete it.')
            return redirect(request.referrer)
        else:
            return render_template('delete.html', rows = postsDict, loginbanner=loginbanner)
    else:
        flash('You need to login before deleting posts.')
        return redirect(url_for('homePage'))
        
    
@app.route('/manageCourses', methods=['GET', 'POST'])
def manageCourses():
    """Function allows admins to delete courses."""
    conn = courseBrowser.getConn('c9')
    loginbanner = ""
    conn = getConn('c9')
    if 'uid' in session:
        if session['isAdmin']:
            loginbanner = "Logged in as " + session['name']
            
            if (request.method == 'POST'):
                deleteList = request.form.getlist('deleteCourse')
                for cid in deleteList:
                    courseBrowser.deleteCourse(conn, cid)
                flash('Courses successfullyl deleted.')
            courses = courseBrowser.getSearchResults(conn, "", "", "")

            return render_template('manageCourses.html', loginbanner=loginbanner, courses=courses)
    flash("You need to be logged in as an administrator in order to manage courses.")
    return redirect(url_for('homePage'))
    
@app.route('/editCourse/<cid>', methods=['GET', 'POST'])
def editCourse(cid):
    """Function allows admins to change the professor of a specific course."""
    conn = getConn('c9')
    if 'uid' in session:
        if session['isAdmin']:
            loginbanner = "Logged in as " + session['name']
            
            if (request.method == 'POST'):
                professor = request.form.get('newProf').upper()
                course = courseBrowser.updateCourseProf(conn, cid, professor)
                flash('Course successfully updated.')
                return render_template('editCourse.html', loginbanner=loginbanner, course = course)
            
            course = courseBrowser.getInfoAboutCourse(conn, cid)
            return render_template('editCourse.html', loginbanner=loginbanner, course = course)
    flash("You need to be logged in as an administrator in order to manage courses.")
    return redirect(url_for('homePage'))

@app.route('/upload/', methods=["GET", "POST"])
def file_upload():
    conn = getConn('c9')
    # if request.method == 'POST':
    #   f = request.files['file']
    #   cid = request.form.get('cid')
    #   filename = secure_filename(f.filename)
    #   f.save(filename)
    #   courseBrowser.insertFile(conn, session['uid'], filename, cid)
    #   flash('file uploaded successfully')
    #   return redirect(request.referrer)
		
    if request.method == 'GET':
        return render_template('form.html',src='',nm='')
    else:
        try:
            f = request.files['file']
            fsize = os.fstat(f.stream.fileno()).st_size
            print 'file size is ',fsize
            if fsize > app.config['MAX_UPLOAD']:
                raise Exception('File is too big')
            print("I AM PAST CONDITIONAL")
            mime_type = imghdr.what(f)
            print("ENTERING NEXT CONDITIONAL")
            if mime_type.lower() not in ['jpeg','gif','png']:
                raise Exception('Not a JPEG, GIF or PNG: {}'.format(mime_type))
            filename = secure_filename('{}'.format(mime_type))
            print("GETTING FILENAME")
            filename = secure_filename(f.filename)
            pathname = filename
            print("pathname is: ")
            print(pathname)
            f.save(pathname)
            cid = request.form.get('cid')
            courseBrowser.insertFile(conn, session['uid'], filename, cid)
            flash('Upload successful')
            return redirect(request.referrer)
        except Exception as err:
            flash('Upload failed {why}'.format(why=err))
            return redirect(request.referrer)
    
#we need a main init function
if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0', 8081)
