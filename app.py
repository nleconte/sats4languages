from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:tfJWljfW@localhost/mydatabase'
db = SQLAlchemy(app)

migrate = Migrate(app, db)

@app.route('/')
def index():
    return "Hello, World!"
