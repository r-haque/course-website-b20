#Date: April 5, 2020
#Course: CSCB20
import sqlite3
from flask import Flask, render_template, g, request, session, redirect, url_for, escape, flash

DATABASE = 'assignment3.db'

def get_db():
    # if there is a database, use it
    db = getattr(g, '_database', None)
    if db is None:
        # otherwise, create a database to use
        db = g._database = sqlite3.connect(DATABASE)
    return db


#converts tuples into dictionaries
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

#given a query gets the result of the database
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

#Tells Flask that "this" is the current running app
app = Flask(__name__)
app.secret_key=b'mango'


# this function gets called when the Flask app shuts down
# tears down the database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        # close the database if we are connected to it
        db.close()

def get_name():
    sql = """
        SELECT fName
        FROM LoginTbl
        WHERE username = ?;
        """
    results = query_db(sql, [session['username']], one=False)
    return results[0][0]

def get_full_name():
    sql = """
        SELECT fName, lName
        FROM LoginTbl
        WHERE username = ?;
        """
    results = query_db(sql, [session['username']], one=False)
    return results[0][0] + " " + results[0][1]

def get_id():
    sql = """
        SELECT ID
        FROM LoginTbl
        WHERE username = ?;
        """
    results = query_db(sql, [session['username']], one=False)
    return results[0][0]

def get_user_type():
    sql = """
        SELECT profession
        FROM LoginTbl
        WHERE username = ?;
        """
    results = query_db(sql, [session['username']], one=False)
    return results[0][0]

@app.route('/', methods=['GET','POST'])
def login():
    if request.method=='POST':
        sql = """
            SELECT *
            FROM LoginTbl
            """
        results = query_db(sql, args=(), one=False)
        for result in results:
            if result[1]==request.form['username']:
                    if result[2]==request.form['password']:
                        session['username']=request.form['username']
                        return redirect(url_for('welcome'))                      
        return redirect(url_for('login_fail'))
    else:
        return render_template('loginregnew.html')

@app.route('/loginfailed')
def login_fail():
    flash('Invalid username/password entered')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You were successfully logged out')
    return redirect(url_for('login'))

@app.route('/register.html', methods=['POST','GET'])
def userRegister():
    g.db=sqlite3.connect('assignment3.db')
    if request.method=='POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        username = request.form.get('username')
        password = request.form.get('password')
        profession = request.form.get('profession')
        ID = request.form.get('id')
        sql = ('INSERT INTO LoginTbl (ID,username,password,fName,lName,profession) VALUES(?, ?, ?, ?, ?, ?)')
        g.db.execute(sql,(ID, username, password, firstname, lastname, profession))
        g.db.commit()
        g.db.close()
        flash('You were successfully signed up')
        return redirect(url_for('login'))       
    else:
        return render_template('register.html')

@app.route('/loginregnew')
def tryagain():
    return redirect(url_for('login'))


@app.route('/welcome')
def welcome():
    name = get_name()
    user_type = get_user_type()
    if user_type.lower() == "student":
        return render_template('welcome.html', name=name)
    else:
        return render_template('welcomeInstruct.html', name=name)

@app.route('/index.html')
def insidepage():
    return render_template('index.html')

@app.route('/feedback_form', methods=['POST','GET'])
def feedback():
    g.db=sqlite3.connect('assignment3.db')
    if request.method=='POST':
        instructor = request.form.get('instructors')
        question1 = request.form.get('like')
        question2 = request.form.get('recommend')
        question3 = request.form.get('labs')
        question4 = request.form.get('improve')
        sql = ('INSERT INTO feedback (instructorName,question1,question2,question3,question4) VALUES(?, ?, ?, ?, ?)')
        g.db.execute(sql,(instructor, question1, question2, question3, question4))
        g.db.commit()
        g.db.close()
        return redirect(url_for('generateWelcome'))       
    else:
        return render_template('feedback.html')

@app.route('/calendar.html')
def calendar():
    return render_template('calendar.html')

@app.route('/lectures.html')
def lectures():
    return render_template('lectures.html')

@app.route('/assignments.html')
def assignments():
    return render_template('assignments.html')

@app.route('/labs.html')
def labs():
    return render_template('labs.html')

@app.route('/resources.html')
def resources():
    return render_template('resources.html')

    
#Showing grades to the user
@app.route('/marks')
def printmarks():
    id = get_id()
    db=get_db()
    db.row_factory = make_dicts
    sql= """select * 
            from marks 
            where ID=?
         """
    students = []
    for student in query_db(sql,[id],one=False):
        students.append(student)
    db.close()
    return render_template('marks.html',student=students)

#Showing all grades to the instructor
@app.route('/studentmarks')
def instrMarks():
    db=get_db()
    db.row_factory = make_dicts
    students = []
    for student in query_db('select * from marks',args=(),one=False):
        students.append(student)
    db.close()    
    return render_template('instructMarks.html',student=students)

#Showing feedback to the instructor
@app.route('/feedback')
def instrFeedback():
    feedback = []
    name = get_full_name()
    db=get_db()
    db.row_factory = make_dicts
    for instructor in query_db('select * from feedback where instructorName=?',[name],one=False):
        feedback.append(instructor)
    db.close()   
    return render_template('instructFeedback.html', feedback=feedback)

def smthfeedback():
    feedback = []
    name = get_full_name()
    db=get_db()
    db.row_factory = make_dicts
    for instructor in query_db('select * from feedback where instructorName=?',[name],one=False):
        feedback.append(instructor)
    db.close()   
    return render_template('instructFeedback.html', feedback=feedback)

#Showing remark requests to the instructor
@app.route('/remarks', methods=['POST','GET'])
def remarkrequests():
    g.db=sqlite3.connect('assignment3.db')
    if request.method=='POST':
        student_id=request.form.get('studentid')
        assessment=request.form.get('assessment')
        mark=request.form.get('mark')
        
        if assessment=='Assignment1':
            g.db.execute("UPDATE Marks SET Assignment1=? WHERE ID=?",(mark,student_id))
        elif assessment=='Assignment2':
            g.db.execute("UPDATE Marks SET Assignment2=? WHERE ID=?",(mark,student_id))
        elif assessment=='Assignment3':
            g.db.execute("UPDATE Marks SET Assignment3=? WHERE ID=?",(mark,student_id))
        elif assessment=='Midterm':
            g.db.execute("UPDATE Marks SET Midterm=? WHERE ID=?",(mark,student_id))
        elif assessment=='Labs':
            g.db.execute("UPDATE Marks SET Labs=? WHERE ID=?",(mark,student_id))
        elif assessment=='FinalExam':
            g.db.execute("UPDATE Marks SET FinalExam=? WHERE ID=?",(mark,student_id))
        g.db.commit()
        g.db.close()    
    db=get_db()
    db.row_factory = make_dicts
    remarks = []
    studentids= []
    for remark in query_db('select * from remarkRequest',args=(),one=False):
        remarks.append(remark)
    for id in query_db('select ID from marks',args=(),one=False):
        studentids.append(id)    
    db.close()    
    return render_template('instructRemark.html',remark=remarks,studentid=studentids)

#Allows instructor to enter marks
@app.route('/entermarks', methods=['POST','GET'])
def entermarks():
    g.db=sqlite3.connect('assignment3.db')
    if request.method=='POST':
        student_id=request.form.get('studentid')
        assessment=request.form.get('assessment')
        mark=request.form.get('mark')
        
        if assessment=='Assignment1':
            g.db.execute("UPDATE Marks SET Assignment1=? WHERE ID=?",(mark,student_id))
        elif assessment=='Assignment2':
            g.db.execute("UPDATE Marks SET Assignment2=? WHERE ID=?",(mark,student_id))
        elif assessment=='Assignment3':
            g.db.execute("UPDATE Marks SET Assignment3=? WHERE ID=?",(mark,student_id))
        elif assessment=='Midterm':
            g.db.execute("UPDATE Marks SET Midterm=? WHERE ID=?",(mark,student_id))
        elif assessment=='Labs':
            g.db.execute("UPDATE Marks SET Labs=? WHERE ID=?",(mark,student_id))
        elif assessment=='FinalExam':
            g.db.execute("UPDATE Marks SET FinalExam=? WHERE ID=?",(mark,student_id))
        g.db.commit()
        g.db.close()
    db=get_db()
    db.row_factory = make_dicts
    studentids= []
    for id in query_db('select ID from marks',args=(),one=False):
        studentids.append(id)
    db.close()        
    return render_template('enterMarks.html', studentid=studentids)

#Submit Remark Request
@app.route('/marks/remarkrequest', methods=['POST','GET'])
def studentrequest():
    g.db=sqlite3.connect('assignment3.db')
    if request.method=='POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        ID = request.form.get('studentnumber')
        assessment = request.form.get('testtype')
        reason = request.form.get('reason')    
        sql = ('INSERT INTO remarkRequest (fName,lName,ID,testtype,reason) VALUES(?, ?, ?, ?, ?)')
        g.db.execute(sql,(firstname, lastname, ID, assessment, reason))
        g.db.commit()
        g.db.close()
        return redirect(url_for('printmarks', name = firstname+" "+lastname))        
    else:
        return render_template('remarkrequest.html')

if __name__ == '__main__':
    app.run(debug=True)
