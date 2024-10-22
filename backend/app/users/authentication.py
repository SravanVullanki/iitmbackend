from flask_bcrypt import Bcrypt
from flask import Blueprint, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import RadioField, StringField, PasswordField, SubmitField, BooleanField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, ValidationError
from .models import User
from .admin.models import Admin
from .customer.models import Customer
from werkzeug.security import generate_password_hash, check_password_hash
from .professional.models import Professional
from app import db, enc
from flask import Blueprint, request, jsonify, session, flash, redirect, url_for
import time
import logging
logging.basicConfig(level=logging.DEBUG)
from flask_cors import CORS

bcrypt = Bcrypt()

auth_blueprint = Blueprint("auth_blueprint", __name__)


CORS(auth_blueprint, resources={r"/*": {
    "origins": "http://localhost:8080",  
    "supports_credentials": True         
}})

class SignupForm(FlaskForm):
    role = RadioField("Get Started As", choices=[("customer", "Customer"), ("professional", "Professional")], default="customer")
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("Email", validators=[Email(message="Please enter a valid email address."), DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=20)])
    confirm_password = PasswordField("Confirm Password", validators=[EqualTo("password", message="Passwords must match."), DataRequired(), Length(min=8, max=20)])

    phone_number = StringField("Phone Number", validators=[Optional(), Length(min=10, max=15)])
    address = StringField("Address", validators=[Optional(), Length(max=200)])

    expertise = StringField("Expertise", validators=[Optional(), Length(max=100)])
    experience_years = StringField("Years of Experience", validators=[Optional()])
    pdf_resume = FileField("Upload Resume", validators=[Optional()])

    submit = SubmitField("Signup to Continue")

    def validate(self, extra_validators=None):
        initial_validation = super(SignupForm, self).validate(extra_validators=extra_validators)

        if self.role.data == "customer":
            if not self.phone_number.data:
                self.phone_number.errors.append("Phone Number is required for customers.")
                return False
            if not self.address.data:
                self.address.errors.append("Address is required for customers.")
                return False

        elif self.role.data == "professional":
            if not self.expertise.data:
                self.expertise.errors.append("Expertise is required for professionals.")
                return False
            if not self.experience_years.data:
                self.experience_years.errors.append("Years of experience are required for professionals.")
                return False
            if not self.pdf_resume.data:
                self.pdf_resume.errors.append("Please upload your resume.")
                return False

        return initial_validation

    def registration(self):
        if self.validate():
            hashed_password = enc.generate_password_hash(self.password.data)
            existing_user = User.query.filter_by(username=self.username.data.lower()).first()
            if existing_user:
                self.username.errors.append("This Username already Exists!")
                return False
            
            existing_email = User.query.filter_by(email=self.email.data.lower()).first()
            if existing_email:
                self.email.errors.append("Email Address is already in use.")
                return False

            new_user = User(username=self.username.data.lower(), email=self.email.data.lower(), password=hashed_password, role=self.role.data)
            db.session.add(new_user)
            db.session.commit()

            if self.role.data == "customer":
                new_role = Customer(user_id=new_user.user_id, phone_number=self.phone_number.data, address=self.address.data)
                session["user_id"] = new_user.user_id
            elif self.role.data == "professional":
                new_role = Professional(
                    user_id=new_user.user_id,
                    expertise=self.expertise.data,
                    experience_years=self.experience_years.data,
                    status="Pending" 
                )
                if self.pdf_resume.data:
                    new_role.pdf_resume = self.pdf_resume.data.read()  

            db.session.add(new_role)
            db.session.commit()

           
            return True

        return False

    def validate_username(self, username):
        allowed = "-_"
        username.data = username.data.lower()
        if all(char.isalnum() or char in allowed for char in username.data):
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("This Username already Exists!")
        else:
            raise ValidationError("Username contains invalid characters.")

    def validate_email(self, email):
        email.data = email.data.lower()
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email Address is already in use.")

class LoginForm(FlaskForm):
    user_mail = StringField("Username or Email Address", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login to Your Account")

    def logar(self):
        if self.validate():
            self.user_mail.data = self.user_mail.data.lower()
            user = User.query.filter(
                (User.email == self.user_mail.data) | 
                (User.username == self.user_mail.data)
            ).first()

            if user is None:
                flash("Sorry, Account does not exist!", "failed")
                return False

            if not enc.check_password_hash(user.password, self.password.data):
                flash("Incorrect username or password!", "failed")
                return False

            if user.role == "professional":
                professional = Professional.query.filter_by(user_id=user.user_id).first()
                if professional.status == "Pending":
                    flash("Your application is still under review. Please wait for approval.", "failed")
                    return False
                if professional.flagged=="true":
                    flash("You are flagged. Please wait for approval.", "failed")
                    return False

            elif user.role == "customer":
                customer = Customer.query.filter_by(user_id=user.user_id).first()
                if customer.flagged=="true":
                    flash("You are flagged. Please wait for approval.", "failed")
                    return False

            session["user_id"] = user.user_id
            if self.remember.data:
                session.permanent = True
            return True

        return False


@auth_blueprint.route("/signup", methods=["POST"])
def signup():
    # Check if user is already logged in
    if "user_id" in session:
        return jsonify({'message': 'Already logged in.'}), 200

    # Extract user data from the request
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    # Handle the file upload
    pdf_resume = request.files.get('pdf_resume')

    # Validate the required fields
    if None in (username, email, password, role):
        return jsonify({'error': 'Please provide all required fields.'}), 400

    # Check if username or email already exists
    existing_user = User.query.filter_by(username=username.lower()).first()
    if existing_user:
        return jsonify({'error': 'This Username already exists!'}), 400

    existing_email = User.query.filter_by(email=email.lower()).first()
    if existing_email:
        return jsonify({'error': 'Email Address is already in use.'}), 400

    # Hash the password and create a new user
    hashed_password = bcrypt.generate_password_hash(password)
    new_user = User(username=username.lower(), email=email.lower(), password=hashed_password, role=role)
    
    db.session.add(new_user)
    db.session.commit()

    if role == "customer":
        customer = Customer(user_id=new_user.user_id, phone_number=request.form.get('phone_number'), address=request.form.get('address'))
        db.session.add(customer)
    elif role == "professional":
        professional = Professional(
            user_id=new_user.user_id,
            expertise=request.form.get('expertise'),
            experience_years=request.form.get('experience_years'),
            status="Pending"
        )
        
        # Check if a resume is uploaded
        if pdf_resume:
            professional.pdf_resume = pdf_resume.read()  # Store the file data

        db.session.add(professional)

    db.session.commit()

    return jsonify({'message': 'Account created successfully! Please log in.'}), 201

@auth_blueprint.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if "user_id" in session:
        return jsonify({'message': 'Already logged in.'}), 200

    user_mail = data.get('username')  
    password = data.get('password')

    if None in (user_mail, password):
        return jsonify({'error': 'Please provide both username/email and password.'}), 400

    user = User.query.filter(
        (User.email == user_mail.lower()) | 
        (User.username == user_mail.lower())
    ).first()

    if user is None:
        return jsonify({'error': 'Sorry, Account does not exist!'}), 404

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({'error': 'Incorrect username or password!'}), 401

    if user.role == "professional":
        professional = Professional.query.filter_by(user_id=user.user_id).first()
        if professional.status == "Pending":
            return jsonify({'error': 'Your application is still under review. Please wait for approval.'}), 403
        if professional.flagged == "True":
            return jsonify({'error': 'You are flagged. Please wait for approval.'}), 403

    elif user.role == "customer":
        customer = Customer.query.filter_by(user_id=user.user_id).first()
        if customer.flagged == "True":
            return jsonify({'error': 'You are flagged. Please wait for approval.'}), 403

    session["user_id"] = user.user_id
    return jsonify({'message': 'Login successful.', 'role': user.role}), 200

@auth_blueprint.route("/logout")
def logout():
    session.pop("user_id", None)
    return jsonify({'message': 'Logged out successfully.'}), 200

