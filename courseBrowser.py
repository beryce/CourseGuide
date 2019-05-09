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
    print(userDict)
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
    '''insert or update the user's rating for a course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    if post_exists(conn, uid, cid):
        curs.execute('update posts set rating=%s,hours=%s,comments=%s where uid=%s and cid=%s',(rating,hours,comments,uid,cid))
    else:
        curs.execute('insert into posts(uid, cid, rating, comments, hours) values (%s, %s, %s, %s, %s)',(uid,cid,rating,comments,hours))
    return True    
    
def post_exists(conn, uid, cid):
    ''''check to see if user has already made a post about a given course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('select * from posts where uid=%s and cid=%s',(uid,cid))
    return curs.fetchone()
    
def compute_avgrating(conn, cid):
    '''compute and return the new average rating for given course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('select * from (select cid, avg(rating) from posts group by cid) as t where cid=%s',(cid,))
    return curs.fetchone()['avg(rating)']

def update_avgrating(conn, cid):
    '''update the average rating for given course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    avgrating = compute_avgrating(conn, cid)
    curs.execute('update courses set avg_rating=%s where cid=%s',(avgrating, cid))
    return curs.fetchall()
    
def compute_avghours(conn, cid):
    '''compute and return the new average hours for given course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('select * from (select cid, avg(hours) from posts group by cid) as t where cid=%s', [cid])
    return curs.fetchone()['avg(hours)']
    
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
    curs.execute('select name, entered, rating, comments, hours from posts inner join users where cid = %s and posts.uid = users.uid', [cid])
    return curs.fetchall()
    
def getUserPastPosts(conn, uid):
    '''Return a list of a given users previous posts'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('select pid, usrs.name, entered, rating, comments, hours, cs.name as cName from posts inner join users as usrs inner join courses as cs where posts.uid = %s and posts.uid = usrs.uid and posts.cid = cs.cid', [uid])
    return curs.fetchall()
    
def updateSearch(conn, semester):
    '''Returns the name and semester of all courses for a given fall/spring semester and year.'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    print("SEMESTER: " + str(semester))
    curs.execute('select name, semester from courses where semester = %s', [semester])
    return curs.fetchall()