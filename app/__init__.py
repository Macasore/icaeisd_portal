from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from flask_mail import Mail

db = SQLAlchemy()
login = LoginManager()
migrate = Migrate()
login.login_view = 'auth.login'
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    
    from app.models import User
    
    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    
    return app