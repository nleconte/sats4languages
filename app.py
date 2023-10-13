# app.py
from flask import Flask, session, render_template, redirect, url_for, flash, request
from extensions import db, migrate
import models  # Assuming models.py is in the same directory as app.py
from models import User, Schedule, Lesson 
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SubmitField, validators, BooleanField
from wtforms.validators import DataRequired
from wtforms import StringField, PasswordField, validators
from wtforms.validators import DataRequired, Email


app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:tfJWljfW@localhost/mydatabase'
app.config['SECRET_KEY'] = 'azerty'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # specify what view to load when a user needs to log in

migrate.init_app(app, db)

import requests

# LNBits configuration
STUDENT_API_KEY = '47e1b195f19e4676b700993846c46644'
TEACHER_API_KEY = '47e1b195f19e4676b700993846c46644'
LNBits_URL = 'https://testnet.laisee.org'  # or your own hosted LNBits URL


class LoginForm(FlaskForm):
    email = StringField('Email Address', [validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', [validators.DataRequired()])
    submit = SubmitField('Login')
    remember_me = BooleanField('Remember Me')

class EndClassForm(FlaskForm):
    pass  # For now, it's an empty form. We're using it mainly for CSRF protection.


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_teacher = True if request.form.get('is_teacher') == 'true' else False  # Handle the checkbox

        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('profile'))
        
        new_user = User(username=username, email=email, is_teacher=is_teacher)  # Use the is_teacher variable
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Thanks for registering!')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
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
    
    if current_user.is_teacher:
        # Fetch classes scheduled by the teacher
        scheduled_lessons = Schedule.query.filter_by(teacher_id=current_user.id).all()
    else:
        # Fetch classes scheduled for the student
        scheduled_lessons = current_user.scheduled_lessons_as_student
    
    scheduled_lessons_count = len(scheduled_lessons)
    return render_template('profile.html', user=user, scheduled_lessons_count=scheduled_lessons_count, scheduled_lessons=scheduled_lessons)

from datetime import datetime

@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    user_id = current_user.id # Using flask-login's current_user

    if request.method == 'POST':
        date_str = request.form.get('date')
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')

        # If a teacher, set availability. If a student, book a lesson.
        if current_user.is_teacher:
            schedule = Schedule(available_date=date_obj, teacher_id=user_id)
            db.session.add(schedule)
            flash('Availability set successfully!')
        else:
            teacher_id = request.form.get('teacher_id')  
            available_schedule = Schedule.query.filter_by(available_date=date_obj, teacher_id=teacher_id, student_id=None).first()
            if available_schedule:
                available_schedule.student_id = user_id
                flash('Lesson booked successfully!')
            else:
                flash('Sorry, this slot is not available.')
                
        db.session.commit()
        return redirect(url_for('profile'))

    teachers = User.query.filter_by(is_teacher=True).all()
    return render_template('schedule.html', teachers=teachers)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))  # Already logged in
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):  # Assuming you have a method called check_password in your User model
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
        flash('Invalid username or password')
    return render_template('login.html', title='Sign In', form=form)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/create_invoice', methods=['POST'])
def create_invoice():
    amount = request.form.get('amount')  # amount in sats

    data = {
        'out': False,
        'amount': amount,
        'memo': 'Load Wallet'
    }

    response = requests.post(f'{LNBits_URL}/api/v1/payments', headers=HEADERS, json=data)
    if response.status_code == 201:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to create invoice"}), 400

@app.route('/check_invoice/<invoice_id>', methods=['GET'])
def check_invoice(invoice_id):
    response = requests.get(f'{LNBits_URL}/api/v1/payments/{invoice_id}', headers=HEADERS)
    return jsonify(response.json())



@app.route('/start_class/<int:class_id>', methods=['POST'])
@login_required
def start_class(class_id):
    # Check if the current user is a student
    if not current_user.is_teacher:
        flash('Only teachers can start a class.')
        return redirect(url_for('profile'))

    class_details = Lesson.query.get(class_id)
    if class_details is None:
        flash("Lesson not found.", "error")
        return redirect(url_for('profile'))


    # Create an invoice on LNBits using student's API key
    headers = {
        'X-Api-Key': STUDENT_API_KEY
    }

    data = {
        'out': True,
        'amount': class_details.cost,
        'memo': f'Lesson Payment for Lessson ID {class_id}'
    }
    response = requests.post(f'{LNBits_URL}/api/v1/payments', headers=HEADERS, json=data)
    payment_data = response.json()

    if 'checking_id' not in payment_data:
        flash('Error creating payment. Ensure you have sufficient funds.')
        return redirect(url_for('index'))

    # TODO: Store payment_data['checking_id'] to verify payment later.
    # For now, we're assuming payment was successful.

    flash('Lesson started successfully. Payment initiated.')
    return redirect(url_for('profile'))

@app.route('/end_class/<int:class_id>', methods=['POST'])
def end_class(class_id):
    class_details = Schedule.query.get(class_id)
    
    if not class_details:
        return jsonify({'message': 'Class not found'}), 404

    # If both confirmed, release the payment to the teacher
    if (
        class_details.status_student == "confirmed-by-student"
        and class_details.status_teacher == "confirmed-by-teacher"
    ):
        teacher = User.query.get(class_details.teacher_id)
        
        # Make a payout request using teacher's API key
        headers = {
            'X-Api-Key': teacher.api_key  # Assuming each teacher has an API key stored in their record
        }
        data = {
            'amount': class_details.cost,
            'memo': f'Lesson Payment for Lesson ID {class_id}'
        }
        response = requests.post(f'{LNBits_URL}/api/v1/payments', headers=headers, json=data)
        payment_data = response.json()

        if 'checking_id' not in payment_data:
            flash('Error transferring funds to teacher. Please check.')
            return redirect(url_for('index'))

        class_details.status = "completed"

    db.session.commit()
    flash('Lesson confirmation successful.')
    return redirect(url_for('profile'))



# Define a form for class creation
class LessonForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Description')
    duration = IntegerField('Duration', validators=[DataRequired()])
    material_link = StringField('Material Link')
    cost = FloatField('Cost', validators=[DataRequired()])
    submit = SubmitField('Create Lesson')

@app.route('/create_class', methods=['GET', 'POST'])
@login_required
def create_class():
    form = LessonForm()
    if form.validate_on_submit():
        new_class = Lesson(
            title=form.title.data,
            description=form.description.data,
            duration=form.duration.data,
            material_link=form.material_link.data,
            cost=form.cost.data
        )
        db.session.add(new_class)
        db.session.commit()
        flash('Lesson created successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('create_class.html', form=form)


@app.route('/ongoing_class/<int:class_id>', methods=['GET', 'POST'])
def ongoing_class(class_id):
    form = EndClassForm()
    
    if form.validate_on_submit():
        # Logic to handle form submission goes here
        pass

    return render_template('ongoing_class.html', class_id=class_id, form=form)



