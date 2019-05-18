from flask import (Flask, url_for, render_template, request, redirect, flash, session, json, jsonify, send_from_directory, Response)
from werkzeug import secure_filename
import MySQLdb
import math, random, string
import courseBrowser
import os
import bcrypt
import imghdr

app = Flask(__name__)

app.secret_key = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

# File uploads
app.config['UPLOADS'] = 'uploads'
app.config['MAX_UPLOAD'] = 256000

''' Route for a home page and renders the home template.'''
@app.route('/')
def homePage():
    if 'name' in session:
        loginbanner = "Logged in as " + session['name']
        return render_template('index.html', loginbanner=loginbanner)
    else:
        return render_template('index.html', loginbanner="")
    
@app.route('/logout/', methods=['GET', 'POST'])
def logout():
    """Function for logging out a user."""
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("homePage"))

@app.route('/addCourse/')
def add_course():
    loginbanner=""
    if 'name' in session:
        loginbanner = "Logged in as " + session['name']
    return render_template('addcourse.html', loginbanner=loginbanner)
 
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
    dummyCourses = courseBrowser.getSearchResults(conn, "", "", "", "", "")
    
    # FOR NOW: global admin password == 'admin'
    isAdmin = "0"
    session['isAdmin'] = False
    if adminPW == 'admin':
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
        uid = session['uid']
        
        # add isFav key to mark if course is starred in dummyCourses dict
        newDummyCourses = courseBrowser.add_isFav_to_Dict(conn, dummyCourses, uid)
                
        return render_template('search.html', loginbanner = "Logged in as " + str(tryToLoginDict['name']), courses=newDummyCourses, uid=uid, filterList=None)
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
# <<<<<<< HEAD
#         session['uid'] = tryToLoginDict['uid']
#         session['username'] = tryToLoginDict['name']
#         uid = session['uid']
        
#         # add isFav key to mark if course is starred in dummyCourses dict
#         newDummyCourses = courseBrowser.add_isFav_to_Dict(conn, dummyCourses, uid)
        
#         return render_template('search.html', loginbanner = "New user created. Logged in as " + str(tryToLoginDict['name']), courses=newDummyCourses, uid=uid)
# =======
        flash("Sorry, we don't recognize that account.")

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
        filter_by = request.form.get('filter_by', "")
        sort_by = request.form.get('sort_by', "")
    else:
        searchterm = request.args.get('searchterm', "")
        semester = request.args.get('semester_filter', "")
        prof = request.args.get('professor_filter', "")
        filter_by = request.form.get('filter_by', "")
        sort_by = request.args.get('sort_by', "")
    
    filterList = {'searchterm': searchterm, 'semester': semester, 'professor': prof, 'filter_by': filter_by, 'sort_by': sort_by}
    
    uid = session.get('uid', False)
    courses = courseBrowser.getSearchResults(conn, searchterm, semester, prof, filter_by, sort_by)
    
    # add isFav key to mark if course is starred in coursesdict
    newCourses = courseBrowser.add_isFav_to_Dict(conn, courses, uid)
    
    return render_template('search.html', courses=courses, loginbanner=loginbanner, filterList=filterList, uid=uid)
    
@app.route('/createPost/<cid>', methods=['GET', 'POST'])
def createPost(cid):
    """Function that redirects to the review page and allows users to create a 
    review for a particular course"""
    
    conn = courseBrowser.getConn('c9')
    uid = session.get('uid', False)
    
    edit_post = {'hours': "", 'comments': ""}
    
    if not uid:
        flash("Sorry, you have to log in before writing a review.")
        return redirect(url_for('homePage'))
    else:
        # check to see if this is an edit post request instead of a create post request
        isEditPostRequest = request.form.get('editPostRequest', False)
        edit_post = {}
        if isEditPostRequest:
            edit_post = {
                'uid': session['uid'],
                'rating': request.form.get('rating', ''),
                'hours': request.form.get('hours', ''),
                'comments': request.form.get('comments', '') 
            }
        # get information about particular course
        courseInfo = courseBrowser.getInfoAboutCourse(conn, cid)
        pastPosts = courseBrowser.get_past_posts(conn, cid)
        if 'name' in session:
            loginbanner = "Logged in as " + session['name']
        return render_template('post.html', course = courseInfo, rows = pastPosts, loginbanner=loginbanner, edit_post=edit_post)

@app.route('/editPosts/', methods=['GET', 'POST'])
def editPosts():  
    """Show a user's previous posts only after a user has successfully logged in"""
    conn = courseBrowser.getConn('c9')
    uid = session.get('uid', False)
    if not uid:
        flash("You need to log in before you can edit your posts.")
        return redirect(url_for('homePage'))
    else:
        loginbanner = "Logged in as " + session['name']
        posts = courseBrowser.getUserPastPosts(conn, uid)
        return render_template('allPosts.html', posts = posts, loginbanner=loginbanner)
    
@app.route('/insertCourse', methods = ["POST"])
def insertCourse():
    """Inserts a new course into the database and displays it on webpage"""
    conn = courseBrowser.getConn('c9')
    
    uid = session.get('uid', False)
    
    # ensure that user is log in before they add a course
    if not uid:
        flash("Sorry, you have to log in first before adding a course.")
        return redirect(url_for('homePage'))
    else:
        # grab name and semester from form
        name = request.form.get("newcoursename")
        semester = request.form.get("newsemester").upper().encode("utf-8")
        professor = request.form.get("newprofessor")
        if (len(semester) != 3) or (semester[0]!='F' and semester[0]!='S') or (not (semester[1:].isdigit())):
            flash("Invalid semester.")
            redirect(url_for("search"))
        elif (len(professor) <= 0):
            flash("Must enter input for professor.")
            redirect(url_for("search"))
        elif len(name) <= 0:
            flash("Must enter new course name.")
            redirect(url_for("search"))
        else:
            if courseBrowser.insertCourse(conn, professor, name, semester, uid):
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
        rating = request.form.get('stars', '')
        hours = request.form.get('fname', '')
        comments = request.form.get('comment')
        
        if rating == '' or hours == '':
            flash("Please enter a review.")
        else:
            result = courseBrowser.rate_course(conn, uid, cid, rating, hours, comments)
            flash('The new average rating is {} and the new average hours are {}.'.format(result['avgrating'], result['avghours']))
    else:
        flash('You need to login!')
    return redirect(request.referrer)

@app.route('/delete', methods=['GET', 'POST']) 
def delete():
    """ Function allows users can delete their posts. """
    conn = courseBrowser.getConn('c9')
    loginbanner = ""
    if 'uid' in session and session['uid'] is not None:
        uid = session['uid']
        if 'name' in session:
            loginbanner="Logged in as " + session['name']
        else:
            loginbanner="Please log in."
        
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
    if 'uid' in session:
        if session['isAdmin']:
            loginbanner = "Logged in as " + session['name']
            
            if (request.method == 'POST'):
                deleteList = request.form.getlist('deleteCourse')
                for cid in deleteList:
                    courseBrowser.deleteCourse(conn, cid)
                flash('Courses successfully deleted.')
            courses = courseBrowser.getSearchResults(conn, "", "", "", "", "")

            return render_template('manageCourses.html', loginbanner=loginbanner, courses=courses)
    flash("You need to be logged in as an administrator in order to manage courses.")
    return redirect(url_for('homePage'))
    
@app.route('/editCourse/<cid>', methods=['GET', 'POST'])
def editCourse(cid):
    """Function allows admins to change the professor of a specific course."""
    conn = courseBrowser.getConn('c9')
    if 'uid' in session:
        if session['isAdmin']:
            loginbanner = "Logged in as " + session['name']
            
            if (request.method == 'POST'):
                professor = request.form.get('newProf')
                course = courseBrowser.updateCourseProf(conn, cid, professor)
                flash('Course successfully updated.')
                return render_template('editCourse.html', loginbanner=loginbanner, course = course)
            
            course = courseBrowser.getInfoAboutCourse(conn, cid)
            return render_template('editCourse.html', loginbanner=loginbanner, course = course)
    flash("You need to be logged in as an administrator in order to manage courses.")
    return redirect(url_for('homePage'))

@app.route('/upload/', methods=["GET", "POST"])
def file_upload():
    conn = courseBrowser.getConn('c9')
    if request.method == 'GET':
        return render_template('form.html',src='',nm='')
    else:
        try:
            f = request.files['file']
            pid = request.form.get('pid', 1)
            fsize = os.fstat(f.stream.fileno()).st_size
            print 'file size is ',fsize
            if fsize > app.config['MAX_UPLOAD']:
                raise Exception('File is too big')
            mime_type = imghdr.what(f)
            if mime_type.lower() not in ['jpeg','gif','png', 'pdf']:
                raise Exception('Not a JPEG, GIF or PNG: {}'.format(mime_type))
            filename = secure_filename('{}.{}'.format(pid, mime_type))
            pathname = os.path.join(app.config['UPLOADS'], filename)
            f.save(pathname)
            courseBrowser.insertFile(conn, pid, filename)
            flash('Upload successful')
            return redirect(request.referrer)
        except Exception as err:
            flash('Upload failed {why}'.format(why=err))
            return redirect(request.referrer)

@app.route('/pic/<path>')
def pic(path):
    """Returns the picture associated with given pid."""
    conn = courseBrowser.getConn('c9')
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    return send_from_directory(app.config['UPLOADS'], path)
    # val = send_from_directory(app.config['UPLOADS'],row['filename'])
    # return val

@app.route('/createAccount/')
def createAccount():
    """Renders template for users to create an account and join."""
    return render_template('createAccount.html')

@app.route('/join', methods=['POST'])
def join():
    """Function to create a new user"""
    conn = courseBrowser.getConn('c9')
    username = request.form.get('username')
    pw = request.form.get('password')
    adminPW = request.form.get('adminPW')
    
    # course examples displayed after successful login
    dummyCourses = courseBrowser.getSearchResults(conn, "", "", "", "", "")
    
    # FOR NOW: global admin password == 'admin'
    isAdmin = "0"
    session['isAdmin'] = False
    if adminPW == 'admin':
        isAdmin = "1"
        session['isAdmin'] = True
    # query the database to see if there is a matching username and password
    if username == "" or pw == "":
        flash("Please enter a username and password.")
        return render_template('createAccount.html')
    tryToLoginDict = courseBrowser.getUser(conn, username, pw, isAdmin)
    # valid login and pw
    if tryToLoginDict['response'] == 0:
        flash("Sorry, that account already exists.")
        return render_template('createAccount.html')
    # incorrect pw entered
    # if the username exists in the database but the password is wrong,
    # flash a warning to the user and redirect
    if tryToLoginDict['response'] == 1:
        flash("Sorry, that account already exists.")
        return render_template('createAccount.html')
    # if the username is not in the database, then 
    # update the database by creating a new user with that login and password information
    # creating a new user with entered username and pw
    else:
        newUser = courseBrowser.createUser(conn, username, pw, isAdmin)
        session['uid'] = newUser['uid']
        session['username'] = newUser['name']
        session['name'] = newUser['name']
        return render_template('search.html', loginbanner = "New user created. Logged in as " + str(newUser['name']), filterList = None, courses=dummyCourses)

    return redirect(url_for('homePage'))
    
@app.route('/favCourses/', methods=['GET', 'POST'])
def fav_courses():
    conn = courseBrowser.getConn('c9')
    if 'uid' in session:
        uid = session.get('uid')
        favCourses = courseBrowser.get_fav_courses(conn, uid)
        return render_template('favCourses.html', courses = favCourses)
        
    flash("Sorry, you have to log in before writing a review.")
    return redirect(url_for('homePage'))

@app.route('/starCourseAjax/', methods=['GET', 'POST'])
def star_course_ajax():    
    cid = request.form.get('cid')
    isFav = request.form.get('isFav')
    if 'uid' in session:
        uid = session['uid']
        conn = courseBrowser.getConn('c9')
        courseBrowser.starCourse(conn, uid, cid, isFav)
        return jsonify( {} )
    
    flash("Sorry, you have to log in before writing a review.")
    return redirect(url_for('homePage'))

#we need a main init function
if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0', 8081)
