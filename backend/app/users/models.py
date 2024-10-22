from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "User"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False) 
    name = db.Column(db.String(50), default='No Name')
    admin = db.relationship("Admin", back_populates="user", uselist=False, cascade="all, delete-orphan")
    professional = db.relationship("Professional", back_populates="user", uselist=False, cascade="all, delete-orphan")
    customer = db.relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")


