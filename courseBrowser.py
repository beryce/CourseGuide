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

def getInfoAboutCourse(conn, cid):
    """Gets information about a PARTICULAR couse."""
    #BUG: NEED TO INNER JOIN WITH POSTS BUT POSTS IS BEING WEIRD
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    # curs.execute('''select * from courses where cid = %s''', [cid])
    curs.execute('''select * from courses where courses.cid = %s''', [cid])
    return curs.fetchone()
    
def getUser(conn, username, pw, isAdmin):
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