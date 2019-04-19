import sys
import MySQLdb

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
    
def getUser(conn, username, hashedPW, isAdmin):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''select * from users where name = %s''', [username])
    userDict = curs.fetchone()
    if userDict['hashedPW'] == hashedPW:
        userDict["response"] = 0
    if userDict['hashedPW'] != hashedPW:
        userDict["response"] = 1
    if userDict is None:
        curs.execute('''insert into users (name, hashedPW, isAdmin) values (%s, %s, %s)''', [username, hashedPW, isAdmin])
        curs.execute('''select * from users where name = %s''', [username])
        userDict = curs.fetchone()
        userDict["response"] = 2
    return userDict

def getSearchResults(conn, input_search):
    """Returns the search results with the given input user types into search bar.
    For example, if the user types in "cs", the result will be all classes where
    there is a "cs" in the course name."""
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    term = '%' + input_search + '%'
    curs.execute('select name, cid, semester from courses where name like %s', [term])
    return curs.fetchall()