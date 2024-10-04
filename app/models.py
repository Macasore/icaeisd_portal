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
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    logged_in = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    
class Paper(db.Model):
    __tablename__ = "papers"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    theme = db.Column(db.String(200), nullable=False)
    subtheme = db.Column(db.String(200), nullable=False)
    abstract = db.Column(db.String(350), nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())    
    author = db.relationship('User', backref='papers')
    
    co_authors = db.relationship('CoAuthor', backref='paper', lazy=True, cascade="all, delete-orphan")
    
class CoAuthor(db.Model):
    __tablename__ = 'co_authors'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)

    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=False)

    def __repr__(self):
        return f"<CoAuthor(full_name={self.full_name}, email={self.email})>"