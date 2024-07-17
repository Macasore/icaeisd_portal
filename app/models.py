from app import db
from flask_login import UserMixin
import enum

class Role(enum.Enum):
    AUTHOR = 'author'
    REVIEWER = 'reviewer'
    EDITOR = 'editor'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)