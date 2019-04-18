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