import sys
import MySQLdb
import bcrypt
from threading import Lock
lock = Lock()

def getConn(db):
    """Function to connect to the passed-in database."""
    conn = MySQLdb.connect(host='localhost',
                           user='ubuntu',
                           passwd='',
                           db=db)
    conn.autocommit(True)
    return conn
    
def getCoursesWithTitle(conn, title):
    """Gets name, cid, semester, avg_rating, avg_hours for ALL courses with similar name."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''select * from courses where name like %s''', ['%' + title + '%'])
    return curs.fetchall()

def insertCourse(conn, professor, name, semester, uid):
    """Inserts a new course with given name and semester into course database."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    lock.acquire()
    #first check if the information is already a course in the database
    didInsert = False
    curs.execute('select name, professor, semester from courses where name=%s and semester=%s and professor=%s', (name, semester, professor))
    if (curs.fetchone() is None):
        curs.execute('insert into courses(name, semester, professor, avg_rating, avg_hours) values (%s, %s, %s, 0, 0) on duplicate key update name = %s, semester = %s, professor = %s', 
                (name, semester, professor, name, semester, professor))
        
        # add course to favorites database
        cid = curs.execute('select cid from courses where name=%s and semester=%s and professor=%s',(name, semester, professor))
        isFavDict = fav_course_exists(conn, uid, cid)
        if isFavDict:
            isFav = 1 if isFavDict['isFav'] == 0 else 0
            starCourse(conn, uid, cid, isFav)
        else:
            starCourse(conn, uid, cid, 0)
        
        didInsert = True
    lock.release()
    return didInsert
    
def updateCourseProf(conn, cid, professor):
    """Updates the professor of a specific course given the cid."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('update courses set professor=%s where cid = %s', [professor, cid])
    ret = getInfoAboutCourse(conn, cid)
    return ret

def getInfoAboutCourse(conn, cid):
    """Gets information about a PARTICULAR couse."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''select * from courses where courses.cid = %s''', [cid])
    return curs.fetchone()
    
def getUser(conn, username, pw, isAdmin):
    """Gets information about a particular user. Checks to see if the password 
    is a match and whether or not they are an admin."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''select * from users where name = %s''', [username])
    userDict = curs.fetchone()
    if userDict is not None:
        hashedPW = bcrypt.hashpw(pw.encode('utf-8'), userDict['hashedPW'].encode('utf-8'))
        # user and password match what is in the database
        if userDict['hashedPW'] == hashedPW:
            userDict['response'] = 0
            # if the user exists but now they have the admin password (or did not enter an admin password), 
            # then update their admin information in the database
            curs.execute('''update users set isAdmin = %s where uid = %s''', [isAdmin, userDict['uid']]);
        # user exists but password does not match
        if userDict['hashedPW'] != hashedPW:
            userDict['response'] = 1
        return userDict
    # username does not exist in the database, create new user
    else:
        return {"response": 2}
    return userDict
    
def createUser(conn, username, pw, isAdmin):
    """Creates a new user."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    hashedPW = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
    lock.acquire()
    curs.execute('''insert into users (name, hashedPW, isAdmin) values (%s, %s, %s)''', [username, hashedPW, isAdmin])
    curs.execute('''select * from users where name = %s''', [username])
    lock.release()
    userDict = curs.fetchone()
    userDict['response'] = 2
    return userDict

def getSearchResults(conn, input_search, input_semester, input_prof, filter_by, sort_by):
    """Returns the name, cid, semester for the given course name user types into search bar.
    For example, if the user types in "cs", the result will be all classes where
    there is a "cs" in the course name. """
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    name = '%' + input_search + '%'
    sem = '%' + input_semester + '%'
    prof = '%' + input_prof + '%'
    
    if filter_by == "average rating":
        if sort_by == "low to high":
            curs.execute('select name, cid, semester, professor, avg_hours, avg_rating from courses where name like %s and semester like %s and professor like %s group by cid order by avg_rating asc', [name, sem, prof])
        else:
            curs.execute('select name, cid, semester, professor, avg_hours, avg_rating from courses where name like %s and semester like %s and professor like %s group by cid order by avg_rating desc', [name, sem, prof])
    else:
        if sort_by == "low to high":
            curs.execute('select name, cid, semester, professor, avg_hours, avg_rating from courses where name like %s and semester like %s and professor like %s group by cid order by avg_hours asc', [name, sem, prof])
        else:
            curs.execute('select name, cid, semester, professor, avg_hours, avg_rating from courses where name like %s and semester like %s and professor like %s group by cid order by avg_hours desc', [name, sem, prof])
    
    return curs.fetchall()
    
def rate_course(conn, uid, cid, rating, hours, comments): 
    '''insert or update the user's rating and hours for a course, then computes the new average rating and hours for a course
    and updates the courses table'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    
    alreadyExists = post_exists(conn, uid, cid)
    
    # insert new post into the database or update it if post already exists
    # tried doing it with on duplicate key update, but because of the way we set
    # up our tables, it wasn't updating correctly
    # maybe try using a composite primary key? unsure
    # anyway, I tried to fix it using a helper function to see if post already exists
    if alreadyExists is not None:
        pid = alreadyExists['pid']
        curs.execute('update posts set rating=%s,hours=%s,comments=%s where uid=%s and cid=%s', [rating,hours,comments,uid,cid])
    else:
        curs.execute('insert into posts(uid, cid, rating, comments, hours) values (%s, %s, %s, %s, %s)', [uid,cid, rating, comments, hours])
        
    # calculate the new average rating and average hours for the given class
    avg_rating = compute_avgrating(conn, cid)
    avg_hours = compute_avghours(conn, cid)
    
    # update the class in courses table with new average rating and new average hours
    update_avgrating(conn, cid)
    update_avghours(conn, cid)
    
    return {'avgrating': avg_rating, 'avghours': avg_hours}

def post_exists(conn, uid, cid):
    ''''check to see if user has already made a post about a given course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('select * from posts where uid=%s and cid=%s',(uid,cid))
    return curs.fetchone()
    
def compute_avgrating(conn, cid):
    '''compute and return the new average rating for given course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    # curs.execute('select * from (select cid, avg(rating) from posts group by cid) as t where cid=%s',(cid,))
    curs.execute('select avg(rating) from (select * from posts where cid = %s) as t1', [cid])
    result = curs.fetchone()
    if result is not None:
        return result['avg(rating)']
    else:
        return 0.0
        
def update_avgrating(conn, cid):
    '''update the average rating for given course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    avgrating = compute_avgrating(conn, cid)
    curs.execute('update courses set avg_rating=%s where cid=%s',(avgrating, cid))
    return curs.fetchall()

def compute_avghours(conn, cid):
    '''compute and return the new average hours for given course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    # curs.execute('select * from (select cid, avg(hours) from posts group by cid) as t where cid=%s', [cid])
    curs.execute('select avg(hours) from (select * from posts where cid = %s) as t1', [cid])
    result = curs.fetchone()
    if result is not None:
        return result['avg(hours)']
    else: return 0.0
    
def update_avghours(conn, cid):
    '''update the average hours for given course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    avghours = compute_avghours(conn, cid)
    curs.execute('update courses set avg_hours=%s where cid=%s',(avghours, cid))
    return curs.fetchall()
    
def get_past_posts(conn, cid):
    '''Show the rating, time stamp, comments, and hours other people entered in the past 
    for a particular course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('select name, entered, rating, comments, hours, filename, pid from posts inner join users where cid = %s and posts.uid = users.uid order by entered desc', [cid])
    return curs.fetchall()
    
def getUserPastPosts(conn, uid):
    '''Return a list of a given users previous posts'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('select pid, posts.cid as courseId, usrs.name, entered, rating, comments, filename, hours, cs.name as cName from posts inner join users as usrs inner join courses as cs where posts.uid = %s and posts.uid = usrs.uid and posts.cid = cs.cid', [uid])
    return curs.fetchall()

def insertFile(conn, pid, filename):
    """Inserts a file into posts database using given file name."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''insert into posts(pid,filename) values (%s,%s)
                on duplicate key update filename = %s''',
                [pid, filename, filename])
                
# same as getUserPastPosts --delete getUserPastPosts
def getAllPosts(conn, uid):
    """Returns all posts for a given uid"""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('select courses.name, posts.cid, posts.hours, posts.rating, posts.entered, posts.comments, posts.filename from posts inner join courses on posts.cid = courses.cid where posts.uid = %s order by hours desc', (uid,))
    postsDict = curs.fetchall()
    return postsDict
    
def deletePost(conn, uid, cid):
    """Deletes a single post made by a user"""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('delete from posts where cid = %s and uid = %s', [cid, uid])
    update_avgrating(conn, cid)
    update_avghours(conn, cid)
    
    
def deleteCourse(conn, cid):
    """Deletes a single course listing and all posts associated with it. In our
    tables, we have an on delete cascade setting."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    print("DELETING THE FOLLOWING COURSES")
    print(cid)
    curs.execute('delete from courses where cid = %s', [cid])
    
def get_fav_courses(conn, uid):
    """Get a user's favorite courses given their uid"""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute("select courses.name,courses.semester,courses.professor from favorites inner join courses on favorites.cid = courses.cid where uid=%s and isFav='1'", [uid])
    return curs.fetchall()
    
def starCourse(conn, uid, cid, isFav):
    """Get a user's favorite courses given their uid"""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('insert into favorites(uid, cid, isFav) values (%s, %s, %s) on duplicate key update isFav=%s', (uid, cid, isFav, isFav))
    return curs.fetchall()
    
def fav_course_exists(conn, uid, cid):
    ''''check to see if user has already made a post about a given course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('select isFav from favorites where uid=%s and cid=%s',(uid,cid))
    return curs.fetchone()

def add_isFav_to_Dict(conn, courses, uid):
    for course in courses:
        print('isfav', fav_course_exists(conn, uid, course['cid']))
        if fav_course_exists(conn, uid, course['cid']):
            course['isFav'] = fav_course_exists(conn, uid, course['cid'])['isFav']
        else:
            course['isFav'] = 0
    return courses
