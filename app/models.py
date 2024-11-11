from app import db
from flask_login import UserMixin
import enum
from sqlalchemy.sql import func

class Role(enum.Enum):
    AUTHOR = 'author'
    REVIEWER = 'reviewer'
    EDITOR = 'editor'
    ATTENDEE = 'attendee'
    ADMIN = 'admin'
    
class PaperStatus(enum.Enum):
    A = 'accepted'
    R = 'rejected'
    P = 'pending'
    AMAR = 'accept with major revision'
    AMIR = 'accept with minor revision'
    CUR = 'currently under review'
    RF = 'review feedback'
    

class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), unique=True, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    payment_confirmed = db.Column(db.Boolean, default=False)
    payment_path = db.Column(db.String(100), nullable=True)
    logged_in = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(255), nullable=True)
    role = db.Column(db.Enum(Role), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    otp = db.Column(db.String(255), nullable=True)
    otp_expiry = db.Column(db.DateTime(timezone=True))
    otp_confirmed = db.Column(db.Boolean, default=False)
    assigned_theme = db.Column(db.String(255), nullable=True)
    
    papers = db.relationship('Paper', backref='author', cascade='all, delete-orphan', foreign_keys='Paper.author_id')
    
    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email_address': self.email,
            'phone_number': self.phone_number,
            'is_paid': self.is_paid,
            'role': self.role.name,
            'theme': self.assigned_theme
        }
class Paper(db.Model):
    __tablename__ = "papers"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    theme = db.Column(db.String(200), nullable=False)
    subtheme = db.Column(db.String(200), nullable=False)
    abstract = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    payment_confirmed = db.Column(db.Boolean, default=False)
    payment_path = db.Column(db.String(100), nullable=True)
    paper_status = db.Column(db.Enum(PaperStatus), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())    
    author = db.relationship('User', backref='papers', foreign_keys=[author_id])
    review_comment = db.Column(db.Text, nullable=True)
    reviewer_count = db.Column(db.Integer, default=0)

    
    review_history = db.relationship('ReviewHistory', back_populates='paper')

    co_authors = db.relationship('CoAuthor', backref='paper', lazy=True, cascade="all, delete-orphan")
    
    def serialize(self):
        return {
            'id': self.id,
            'author_firstname': self.author.first_name,
            'author_lastname': self.author.last_name,
            'title': self.title,
            'theme': self.theme,
            'subtheme': self.subtheme,
            'abstract': self.abstract,
            'user_id': self.author_id,
            'file_url': self.file_path,
            'paper_status': self.paper_status.name,
            'is_paid': self.is_paid,
            'payment_confirmed': self.payment_confirmed,
            'payment_path': self.payment_path,
            'created_at': self.created_at.isoformat(),
            'reviewer_count': self.reviewer_count,
            'co_authors': [coauthor.serialize() for coauthor in self.co_authors],
            'reviews': [review.serialize() for review in self.review_history] 
        }

class CoAuthor(db.Model):
    __tablename__ = 'co_authors'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=False)

    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=False)

    def __repr__(self):
        return f"<CoAuthor(first_name={self.first_name},last_name={self.last_name}, email={self.email})>"
    
    def serialize(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email
        }
        

class ReviewHistory(db.Model):
    __tablename__ = 'review_history'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.Enum(PaperStatus), nullable=False) 
    comment = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    review_questions = db.Column(db.Text, nullable=True)
    
    paper = db.relationship('Paper', back_populates='review_history')
    reviewer = db.relationship('User', backref='review_histories')
    
    def serialize(self):
        return {
            'id': self.id,
            'comment': self.comment,
            'status': self.status.name,
            'reviewed_at': self.reviewed_at.isoformat()
        }

class Reviewer(db.Model):
    __tablename__ = 'reviewers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    claimed_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    paper = db.relationship('Paper', backref='reviewers')
    reviewer = db.relationship('User', backref='claimed_reviews')