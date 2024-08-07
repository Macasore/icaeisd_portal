from app import db
from flask_login import UserMixin
import enum
from sqlalchemy.sql import func

class Role(enum.Enum):
    AUTHOR = 'author'
    REVIEWER = 'reviewer'
    EDITOR = 'editor'
    ATTENDEE = 'attendee'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    is_paid = db.Column(db.Boolean, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    
    
