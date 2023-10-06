
from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin



class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_teacher = db.Column(db.Boolean, default=False)
    schedules = db.relationship('Schedule', backref='teacher', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    available_date = db.Column(db.DateTime, default=datetime.utcnow)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
