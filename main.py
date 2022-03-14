# -*- coding: utf-8 -*-
#basic imports
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request,Flask,redirect
from flask_login import LoginManager,login_user,login_required,logout_user,current_user
from datetime import datetime

#app initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quantified_self_database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.app_context().push()
app.config['SECRET_KEY']='myappquantified'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view='/notfound/Unauthorized'
#database import
from database import *

#==============================Business Logic====================================
#------------Login-Logout-------------
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
#-------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method=='POST':
        uname=request.form.get('username')
        passd=request.form.get('password')
        try:
            user=User.query.filter(User.username==uname,User.password==passd).one()
        except:
            return render_template('login.html',error='incorrect password or username')
        if not current_user.is_active:
            login_user(user)
    if current_user.is_active:
        return main()
    else:
        return render_template('login.html')
#---------------------------
@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method=='POST':
        uname=request.form.get('username')
        passd=request.form.get('password')
        if uname not in [i.username for i in User.query.all()]:
            user=User(username=uname,password=passd)
            db.session.add(user)
            db.session.commit()
            return login()
        return redirect('/notfound/User already exists.')
    return render_template("signup.html")
#----------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return login()
#----------------------------
@app.route("/notfound/<error>")
def notfound(error):
    return render_template('notfound.html',error=error)

#-------------------Tracker---------------------------
@app.route('/main')
@login_required
def main():
    return render_template('main.html',user=current_user)

@app.route('/tracker/add',methods=['GET','POST'])
@login_required
def add_tracker():
    if request.method=='POST':
        u_id=current_user.get_id()
        name=request.form.get('name')
        desc=request.form.get('desc')
        type=request.form.get('type')
        set=request.form.get('settings')
        #---validation----
        if name in [i.name for i in User.query.get(u_id).trackers]:
            return notfound('Tracker name should be unique')

        if type!='Integer' and type!='Numeric':
            if set=="":
                return notfound('Tracker setting not valid, Multi-Choice should have setting separated by comma.')
        else:
            if set!="":
                set=""
        #-----------------
        add=tracker(user_id=u_id,name=name,desc=desc,type=type,settings=set)
        try:
            db.session.add(add)
            db.session.commit()
            return main()
        except Exception as e:
            db.session.rollback()
            return(f'-------add_tracker_db_error-------{e}')
    return render_template('add_tracker.html')

@app.route('/tracker/<int:tracker_id>',methods=['GET','POST'])
@login_required
def view_tl(tracker_id):
    t=tracker.query.get(tracker_id)
    return render_template('tracker.html',tracker=t,user=current_user)

@app.route('/tracker/<int:tracker_id>/update',methods=['GET','POST'])
@login_required#*************************
def update_tracker(tracker_id):
    #Validarion
    if (tracker_id,) not in db.session.query(tracker.tracker_id).all():
        return notfound('tracker_id_not_found')
    t=tracker.query.get(tracker_id)
    if request.method=='POST':
        pass

    return render_template('update_tracker.html',tracker=t,user=current_user)

@app.route('/tracker/<int:tracker_id>/delete',methods=['GET','POST'])
@login_required
def delete_tracker(tracker_id):
    t=tracker.query.get(tracker_id)
    try:
        db.session.delete(t)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print('----tracker_delete_dberror------',e)
    return main()
#-----------------------------logs---------------------------
@app.route('/<int:tracker_id>/log/add',methods=['GET','POST'])
@login_required
def add_logs(tracker_id):
    if request.method=='POST':
        l=log(tracker_id=tracker_id,log_datetime=datetime.now(),note=request.form.get('note'),log_value=request.form.get('value'))
        db.session.add(l)
        db.session.commit()
        return main()
    return render_template('add_logs.html',t=tracker.query.get(tracker_id),datetime=datetime)

@app.route('/<int:log_id>/log/update',methods=['GET','POST'])
@login_required
def update_log(log_id):
    if request.method=='POST':
        log_value=request.form.get("value")
        log_note=request.form.get("note")
        log_datetime=datetime.strptime(request.form.get("time"),'%Y-%m-%d %H:%M:%S.%f')
        print(log_datetime)
        db.session.query(log).filter(log.log_id==log_id).update({'log_value':log_value,'note':log_note,'log_datetime':log_datetime})
        db.session.commit()
    return render_template('update_logs.html',log=log.query.get(log_id))

@app.route('/<int:log_id>/log/delete',methods=['GET','POST'])
@login_required
def delete_log(log_id):
    l=log.query.get(log_id)
    t=l.tracker_id
    db.session.delete(l)
    db.session.commit()
    return view_tl(t)

#====================================================================================

if __name__=='__main__':
    app.run(host='0.0.0.0',debug=True)
