import os
from flask import Flask, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from datetime import timedelta
from celery import Celery
import pandas as pd
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
enc = Bcrypt()
login_manager = LoginManager()
mail = Mail()

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    return celery

def create_app():
    Meto = Flask(__name__)

    current_directory = os.path.abspath(os.path.dirname(__file__))
    parent_of_parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
    db_directory = os.path.join(parent_of_parent_directory, "instance", "meto.sqlite3")

    Meto.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_directory
    Meto.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "@Sravan")
    Meto.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
    Meto.config["UPLOAD_FOLDER"] = "app/static/images/profileimages"
    
    Meto.config['MAIL_SERVER'] = 'smtp.gmail.com'
    Meto.config['MAIL_PORT'] = 465
    Meto.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME", 'mikemarcus1201@gmail.com')
    Meto.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD", 'fvazxbcjdxohhdgu')
    Meto.config['MAIL_USE_TLS'] = False
    Meto.config['MAIL_USE_SSL'] = True
    Meto.config['MAIL_DEFAULT_SENDER'] = os.environ.get("MAIL_DEFAULT_SENDER", 'mikemarcus1201@gmail.com')
    
    Meto.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    Meto.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


    db.init_app(Meto)
    enc.init_app(Meto)
    login_manager.init_app(Meto)
    mail.init_app(Meto)
    
    celery = make_celery(Meto)

    from app.users.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @Meto.route("/", methods=["GET"])
    def home():
        return jsonify({'message': 'Welcome to the home page!'}), 200

    from app.users.authentication import auth_blueprint
    from app.users.dashboard_and_operations import dash_blueprint
    Meto.register_blueprint(auth_blueprint, url_prefix="/auth")
    Meto.register_blueprint(dash_blueprint, url_prefix="/dash")

    return Meto

def database_creator(app, db_directory):
    if not os.path.exists(db_directory):
        os.makedirs(os.path.dirname(db_directory), exist_ok=True)
        with app.app_context():
            db.create_all()
            print("Database created and synced")
    else:
        print("Database already exists")
