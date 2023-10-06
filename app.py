# app.py
from flask import Flask, session
from flask import render_template, redirect, url_for, flash, request
from flask import Flask, flash, redirect, url_for, request, render_template
from extensions import db, migrate
import models  # Assuming models.py is in the same directory as app.py
from models import User, Schedule
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:tfJWljfW@localhost/mydatabase'
app.config['SECRET_KEY'] = 'azerty'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # specify what view to load when a user needs to log in

migrate.init_app(app, db)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email, is_teacher=False)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Thanks for registering!')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first!')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if request.method == 'POST':
        # Get updated data
        username = request.form.get('username')
        email = request.form.get('email')
        
        # Update user
        user.username = username
        user.email = email
        
        db.session.commit()
        
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

from datetime import datetime

@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first!')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        schedule = Schedule(available_date=date_obj, teacher_id=user_id)
        
        db.session.add(schedule)
        db.session.commit()
        
        flash('Lesson scheduled successfully!')
        return redirect(url_for('schedule'))
    
    return render_template('schedule.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('profile'))
        
        flash('Login Unsuccessful. Please check email and password', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

