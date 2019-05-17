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

def insertCourse(conn, professor, name, semester):
    """Inserts a new course with given name and semester into course database."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    lock.acquire()
    #first check if the information is already a course in the database
    didInsert = False
    curs.execute('select name, professor, semester from courses where name=%s and semester=%s and professor=%s', (name, semester, professor))
    if (curs.fetchone() is None):
        curs.execute('insert into courses(name, semester, professor, avg_rating, avg_hours) values (%s, %s, %s, 0, 0) on duplicate key update name = %s, semester = %s, professor = %s', 
                (name, semester, professor, name, semester, professor))
        didInsert = True
    lock.release()
    return didInsert
    
def updateCourseProf(conn, cid, professor):
    """Updates the professor of a specific course given the cid."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    lock.acquire()
    print("updating course in COURSE BROWSER...")
    curs.execute('update courses set professor=%s where cid = %s', [professor, cid])
    lock.release()
    ret = getInfoAboutCourse(conn, cid)
    print("UPDATED COURSE INFO")
    print(ret)
    return ret

def getInfoAboutCourse(conn, cid):
    """Gets information about a PARTICULAR couse."""
    #BUG: NEED TO INNER JOIN WITH POSTS BUT POSTS IS BEING WEIRD
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    # curs.execute('''select * from courses where cid = %s''', [cid])
    curs.execute('''select * from courses where courses.cid = %s''', [cid])
    return curs.fetchone()
    
def getUser(conn, username, pw, isAdmin):
    """Gets information about a particular user. Checks to see if the password 
    is a match and whether or not they are an admin."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''select * from users where name = %s''', [username])
    userDict = curs.fetchone()
    print("searching for user in the database...")
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
        hashedPW = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
        print("attempting to insert new user into the database...")
        lock.acquire()
        curs.execute('''insert into users (name, hashedPW, isAdmin) values (%s, %s, %s)''', [username, hashedPW, isAdmin])
        lock.release()
        curs.execute('''select * from users where name = %s''', [username])
        userDict = curs.fetchone()
        userDict['response'] = 2
    return userDict

def getSearchResults(conn, input_search, input_semester, input_prof):
    """Returns the name, cid, semester for the given course name user types into search bar.
    For example, if the user types in "cs", the result will be all classes where
    there is a "cs" in the course name. """
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    name = '%' + input_search + '%'
    sem = '%' + input_semester + '%'
    prof = '%' + input_prof + '%'
    curs.execute('select name, cid, semester, professor, avg_hours, avg_rating from courses where name like %s and semester like %s and professor like %s', [name, sem, prof])
    return curs.fetchall()
    
def rate_course(conn, uid, cid, rating, hours, comments): 
    '''insert or update the user's rating and hours for a course, then computes the new average rating and hours for a course
    and updates the courses table'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    
    # insert new post into the database or update it if post already exists
    curs.execute('insert into posts(uid, cid, rating, comments, hours) values (%s, %s, %s, %s, %s) on duplicate key update uid = %s, cid = %s', [uid,cid, rating, comments, hours, uid, cid])
    
    # calculate the new average rating and average hours for the given class
    avg_rating = compute_avgrating(conn, cid)
    avg_hours = compute_avghours(conn, cid)
    
    # update the class in courses table with new average rating and new average hours
    update_avgrating(conn, cid)
    update_avghours(conn, cid)
    
    return {'avgrating': avg_rating, 'avghours': avg_hours}
    
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
    curs.execute('select name, entered, rating, comments, hours, filename, pid from posts inner join users where cid = %s and posts.uid = users.uid', [cid])
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
    print("DELETING THE FOLLOWING POSTS")
    print(cid)
    lock.acquire()
    curs.execute('delete from posts where cid = %s and uid = %s', [cid, uid])
    lock.release()
    
def deleteCourse(conn, cid):
    """Deletes a single course listing and all posts associated with it"""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    print("DELETING THE FOLLOWING COURSES")
    print(cid)
    lock.acquire()
    curs.execute('delete from courses where cid = %s', [cid])
    lock.release()
    
# def orderByHighestAvgRating(conn):
#     """Returns a list of courses (specifically, their average rating and cid) 
#     and orders them by highest to lowest average rating."""
#     curs = conn.cursor(MySQLdb.cursors.DictCursor)
#     curs.execute('select avg_rating, cid from courses group by cid order by avg_rating desc')
#     return curs.fetchall()

# def orderByLowestAvgRating(conn):
#     """Returns a list of courses (specifically, their average rating and cid) 
#     and orders them by lowest to highest average rating."""
#     curs = conn.cursor(MySQLdb.cursors.DictCursor)
#     curs.execute('select avg_rating, cid from courses group by cid order by avg_rating asc')
#     return curs.fetchall()

# def orderByHighestAvgHours(conn):
#     """Returns a list of courses (specifically, their average rating and cid) 
#     and orders them by highest to lowest average hours."""
#     curs = conn.cursor(MySQLdb.cursors.DictCursor)
#     curs.execute('select avg_hours, cid from courses group by cid order by avg_hours desc')
#     return curs.fetchall()
    
# def orderByLowestAvgHours(conn):
#     """Returns a list of courses (specifically, their average rating and cid) 
#     and orders them by highest to lowest average hours."""
#     curs = conn.cursor(MySQLdb.cursors.DictCursor)
#     curs.execute('select avg_hours, cid from courses group by cid order by avg_hours asc')
#     return curs.fetchall()
