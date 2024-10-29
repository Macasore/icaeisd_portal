from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS

db = SQLAlchemy()
login = LoginManager()
migrate = Migrate()
login.login_view = 'auth.login'
mail = Mail()
jwt = JWTManager()
blacklist = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return jti in blacklist



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    SWAGGER_URL = '/swagger'
    API_URL = '/static/swagger.json'
    
    swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  
    API_URL,
    config={ 
        'app_name': "My Flask API"
    }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    
    from app.models import User
    
    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from app.auth.routes import auth_bp
    from app.authors.routes import author_bp
    from app.payment.routes import payment_bp
    from app.admin.routes import admin_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(author_bp, url_prefix='/author')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    @app.errorhandler(NoAuthorizationError)
    def handle_missing_token_error(e):
        return jsonify({"msg": "Token is missing! Please provide a valid token."}), 401
    
    return app