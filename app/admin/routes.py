from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Role
from app import db
from app.auth.helper import sendEmail, generatePassword, sendDetailsToEmail

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/login', methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    user = User.query.filter_by(username=username).first()
    
    
    if user and check_password_hash(user.password, password):
        
        if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403
        user.logged_in = True
        db.session.commit()
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token
            }), 200
        
    return jsonify({"msg": "Invalid username or password"}), 400

@admin_bp.route('/register', methods=["POST"])
def register():
    data = request.json
    email = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone_number = data.get('phone_number')
    role = data.get('role')
    password = generatePassword()
    username = email
    
    if not email or not first_name or not last_name or not phone_number:
        return jsonify({"msg": "All fields are required"}), 400
    
    if role not in Role._value2member_map_:
        return jsonify({"msg": "Invalid role"}), 400
    
    emailCheck = User.query.filter_by(email=email).first()
    if emailCheck:
        return jsonify({"msg": "Email already exists"}), 400
    
    
    user = User(email=email, first_name=first_name, last_name=last_name, phone_number=phone_number, username=username,
                password=generate_password_hash(password), role=Role(role))
    print(user.role)
    db.session.add(user)
    db.session.commit()
    if user.role != Role.ATTENDEE:
        sendDetailsToEmail(username, password, email)
        return jsonify({"msg": f"Please check your email for login detail"}), 200
    return jsonify({"msg": "Registration successful"}), 200