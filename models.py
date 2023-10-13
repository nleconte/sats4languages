from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from enum import Enum

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_teacher = db.Column(db.Boolean, default=False)
    lnbits_api_key = db.Column(db.String(128))
    
    # User's scheduled lessons as both student and teacher
    scheduled_lessons_as_student = db.relationship('Schedule', backref='student', foreign_keys='Schedule.student_id', cascade='all, delete-orphan')
    scheduled_lessons_as_teacher = db.relationship('Schedule', backref='teacher', foreign_keys='Schedule.teacher_id', cascade='all, delete-orphan')
    
    balance = db.Column(db.Float, default=100000)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))  # Rename to lesson.id
    available_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # Index this as it may be frequently queried
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(TransactionStatus), default=TransactionStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # Indexing the creation time


class Escrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))  # Rename to lesson.id
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # Indexing the creation time

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    material_link = db.Column(db.String(250), nullable=True)  # Links to class materials if any
    cost = db.Column(db.Float, nullable=False)  # The cost associated with taking the class

