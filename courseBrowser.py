import sys
import MySQLdb

def getConn(db):
    conn = MySQLdb.connect(host='localhost',
                           user='ubuntu',
                           passwd='',
                           db=db)
    conn.autocommit(True)
    return conn
    
def getCoursesWithTitle(conn, title):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''select * from courses where title like %s''', ['%' + title + '%'])
    return curs.fetchall()
    
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
        userDict["response"] = 3
    return userDict