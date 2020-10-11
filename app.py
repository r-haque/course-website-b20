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

########## HELPER FUNCTIONS ##########
#gets first name of current user in session
#greets user with name
def get_name():
    sql = """
        SELECT fName
        FROM LoginTbl
        WHERE username = ?;
        """
    results = query_db(sql, [session['username']], one=False)
    return results[0][0]

#gets full name of current user in session
def get_full_name():
    sql = """
        SELECT fName, lName
        FROM LoginTbl
        WHERE username = ?;
        """
    results = query_db(sql, [session['username']], one=False)
    return results[0][0] + " " + results[0][1]

#gets id of current user in session
def get_id():
    sql = """
        SELECT ID
        FROM LoginTbl
        WHERE username = ?;
        """
    results = query_db(sql, [session['username']], one=False)
    return results[0][0]

#gets user type (student/instructor) of current user in session
def get_user_type():
    sql = """
        SELECT profession
        FROM LoginTbl
        WHERE username = ?;
        """
    results = query_db(sql, [session['username']], one=False)
    return results[0][0]

#when registering, checks if username/id already exists in the database
def check_exists(cur_user_name, cur_id):
    sql = """
        SELECT *
        FROM LoginTbl
        WHERE username = ? OR ID=?;
        """
    results = query_db(sql, [cur_user_name, cur_id], one=False)
    return results

##################################################################

########## LOGIN/REGISTRATION PAGES ##########
#login pages
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

#if username/password details don't match, user is redirected
@app.route('/loginfailed')
def login_fail():
    flash('Invalid username/password entered')
    return redirect(url_for('login'))

#logs user out of session
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You were successfully logged out')
    return redirect(url_for('login'))

#gets user registration form
#stores new user registration data in database
@app.route('/register', methods=['POST','GET'])
def userRegister():
    g.db=sqlite3.connect('assignment3.db')
    if request.method=='POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        username = request.form.get('username')
        password = request.form.get('password')
        profession = request.form.get('profession')
        ID = request.form.get('id')

        if len(check_exists(username, ID)) != 0:
            flash('Someone with that username/ID already exists. Please try again.')
            return redirect(url_for('login')) 
            
        sql = ('INSERT INTO LoginTbl (ID,username,password,fName,lName,profession) VALUES(?, ?, ?, ?, ?, ?)')
        g.db.execute(sql,(ID, username, password, firstname, lastname, profession))
        g.db.commit()
        g.db.close()

        if profession.lower() == 'student':
            add_student_to_db(ID, firstname, lastname)
        elif profession.lower() == 'instructor':
            add_instructor_to_db(ID, username, password, firstname, lastname)

        flash('You were successfully signed up!')
        return redirect(url_for('login'))       
    else:
        return render_template('register.html')

#when a new user of type student registers, they are added to the marks and students databases
def add_student_to_db(id, fname, lname):
    g.db=sqlite3.connect('assignment3.db')
    sql = ('INSERT INTO Students VALUES(?, ?, ?)')
    g.db.execute(sql,(id, fname, lname))
    g.db.commit()
    sql = ('INSERT INTO Marks VALUES(?, ?, ?, ?, ?, ?, ?, ?)')
    g.db.execute(sql,(id, None, None, None, None, None, None, fname))
    g.db.commit()
    g.db.close()

#when a new user of type instructor register, they are added to the instructors database
def add_instructor_to_db(id, username, password, fname, lname):
    g.db=sqlite3.connect('assignment3.db')
    sql = ('INSERT INTO Instructors VALUES(?, ?, ?, ?, ?)')
    g.db.execute(sql,(id, username, password, fname, lname))
    g.db.commit()
    g.db.close()

@app.route('/loginregnew')
def tryagain():
    return redirect(url_for('login'))

##################################################################

########## STATIC HTML/CSS PAGES ##########
@app.route('/home')
def insidepage():
    return render_template('index.html')

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/lectures')
def lectures():
    return render_template('lectures.html')

@app.route('/assignments')
def assignments():
    return render_template('assignments.html')

@app.route('/labs')
def labs():
    return render_template('labs.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

##################################################################

########## WELCOME PAGE TO GREET STUDENT/INSTRUCTOR ##########
@app.route('/welcome')
def welcome():
    name = get_name()
    user_type = get_user_type()
    if user_type.lower() == "student":
        return render_template('welcome.html', name=name)
    else:
        return render_template('welcomeInstruct.html', name=name)

##################################################################

########## STUDENT USER PAGES ##########
#lets students leave feedback for instructors
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
        return redirect(url_for('welcome'))       
    db=get_db()
    db.row_factory = make_dicts
    instruct = []
    for i in query_db('select fName, lName from Instructors',args=(),one=False):
        instruct.append(i)
    db.close()
    return render_template('feedback.html', instruct=instruct)
    
#Showing grades to the student
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
    
######################################################################

########## INSTRUCTOR USER PAGES ##########
#Showing all student grades to the instructor
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

#Showing remark requests to the instructor
#lets instructor submit a mark change
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

#lets instructor delete a remark request after it has been dealt with
@app.route('/delete', methods=['POST'])
def delete_request():
    g.db=sqlite3.connect('assignment3.db')
    sql = ('DELETE FROM remarkRequest WHERE feedbackID=?')
    f_id = request.form.get('regrade_info')
    g.db.execute(sql, [f_id])
    g.db.commit()
    g.db.close()
    flash('Regrade request successfully deleted')
    return redirect(url_for('remarkrequests'))

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

if __name__ == '__main__':
    app.run(debug=True)
