from app.models import User
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.helper import generatePassword, sendDetailsToEmail
from app import db
from app.models import Role


auth_bp = Blueprint('auth',__name__ )

@auth_bp.route("/register", methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone_number = data.get('phone_number')
    role = data.get('role')
    password = generatePassword()
    username = first_name
    
    if not email or not first_name or not last_name or not phone_number:
        return jsonify({"msg": "All fields are required"}), 400
    
    if role not in Role.__members__:
        return jsonify({"msg": "Invalid role"}), 400
    
    emailCheck = User.query.filter_by(email=email).first()
    if emailCheck:
        return jsonify({"msg": "Email already exists"}), 400
    
    user = User(email=email, first_name=first_name, last_name=last_name, phone_number=phone_number, username=username,
                password=generate_password_hash(password), is_paid=False, role=Role(role))
    print(user.role)
    db.session.add(user)
    db.session.commit()
    if user.role != Role.ATTENDEE:
        sendDetailsToEmail(username, password, email)
        return jsonify({"msg": "Please check your email for login details"}), 200
    return jsonify({"msg": "Registration successful"}), 200
    
    
