import sys
import MySQLdb
import bcrypt

def getConn(db):
    """Function to connect to the passed-in database."""
    conn = MySQLdb.connect(host='localhost',
                           user='ubuntu',
                           passwd='',
                           db=db)
    conn.autocommit(True)
    return conn
    
def getCoursesWithTitle(conn, title):
    """Gets information about ALL courses with similar name."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''select * from courses where name like %s''', ['%' + title + '%'])
    return curs.fetchall()

def insertCourse(conn, name, semester):
    """Inserts a new course with given name and semester into course database."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    #curs.execute('insert into rating_table2(pid, movie_id, rating) values (%s, %s, %s) on duplicate key update pid = %s, rating = %s', (input_tt, person_id, input_rating))
    curs.execute('insert into courses(name, semester) values (%s, %s) on duplicate key update name = %s, semester = %s', 
                (name, semester, name, semester))

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
            curs.fetchone() # <------------------------ necessary????
        # user exists but password does not match
        if userDict['hashedPW'] != hashedPW:
            userDict['response'] = 1
        return userDict
    # username does not exist in the database, create new user
    else:
        hashedPW = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
        print("attempting to insert new user into the database...")
        curs.execute('''insert into users (name, hashedPW, isAdmin) values (%s, %s, %s)''', [username, hashedPW, isAdmin])
        curs.execute('''select * from users where name = %s''', [username])
        userDict = curs.fetchone()
        userDict['response'] = 2
    print (userDict)
    return userDict

def getSearchResults(conn, input_search):
    """Returns the search results with the given input user types into search bar.
    For example, if the user types in "cs", the result will be all classes where
    there is a "cs" in the course name."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    term = '%' + input_search + '%'
    curs.execute('select name, cid, semester from courses where name like %s', [term])
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
    curs.execute('select * from (select cid, avg(hours) from posts group by cid) as t where cid=%s',(cid,))
    return curs.fetchone()['avg(hours)']
    
def update_avghours(conn, cid):
    '''update the average hours for given course'''
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    avghours = compute_avghours(conn, cid)
    curs.execute('update courses set avg_hours=%s where cid=%s',(avghours, cid))
    return curs.fetchall()
    
