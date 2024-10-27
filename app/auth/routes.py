from datetime import datetime, timedelta
from app.models import User, Role
from flask import Blueprint, request, jsonify
from flask_mail import Message
from app import mail
from werkzeug.security import generate_password_hash, check_password_hash
from app.auth.helper import generateOtp, generatePassword, sendDetailsToEmail, verify_otp, sendEmail
from app import db, jwt, blacklist
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt



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
    
    
@auth_bp.route("/login", methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    
    user = User.query.filter_by(username=username).first()
    
    
    if user and check_password_hash(user.password, password):
        user.logged_in = True
        db.session.commit() 
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 200
        
    return jsonify({"msg": "Invalid username or password"}), 400

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True) 
def refresh():
    current_user = get_jwt_identity() 
    new_access_token = create_access_token(identity=current_user)
    return jsonify({"access_token": new_access_token}), 200

@auth_bp.route("/logout", methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()
    if not user:
        return jsonify({"msg": "Invalid user"}), 400
    
    user.logged_in = False
    db.session.commit() 
    
    blacklist.add(jti)
    return jsonify({"msg": "Successfully logged out"}), 200

@auth_bp.route('/send-email', methods=["POST"])
def send_email():
    data = request.json
    subject = data.get('subject')
    email = data.get('email')
    message = data.get('message')
    name = data.get('name')
    
    message_to_send = f"Name: {name}\n\nEmail: {email}\n\nSubject: {subject}\n\n\nMessage: \n{message}"
    
    return sendEmail("Contact-Us", message_to_send, "icaeisd2024sec@cu.edu.ng")

@auth_bp.route("/user-details", methods=["GET"])
@jwt_required()
def user_details():
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    if user:
        return jsonify({
            "email" : user.email,
            "first_name" : user.first_name,
            "last_name" : user.last_name,
            "phone_number" : user.phone_number
        }), 200
    
    return jsonify({"msg": "User doesn't exist"}), 404
    
@auth_bp.route("/forgot-password", methods=["POST"])
def forgotten_password():
    data = request.json
    email = data.get("email")
    
    user = User.query.filter_by(email = email).first()
    
    if not user:
        return jsonify({"msg": "User with this email does not exist"}), 404
    
    otp = generateOtp()
    user.otp = generate_password_hash(otp)
    user.otp_expiry = datetime.now() + timedelta(minutes=15)
    db.session.commit()
    
    message = f"Your otp for Password reset is {otp}. Otp would expire in 15minutes"
    send_email = sendEmail("Password Reset", message, user.email)
    if send_email[1] == 200: 
        return jsonify({"message": "kindly check your email for an otp."}), 200
    else:
        return jsonify({"error": "Failed to send email."}), send_email[1]
        

@auth_bp.route("/verify-otp", methods=["POST"])
def verifyOtp():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")
    
    user = User.query.filter_by(email=email).first()
    
    if user:
        if not user.otp:
            return jsonify({"msg": "Unauthorized for this operation"}), 403        
        otp_valid = verify_otp(otp, user.otp)
        
        if otp_valid and user.otp_expiry > datetime.now():
            user.otp_confirmed = True
            user.otp = None
            user.otp_expiry= None
            db.session.commit()
            return jsonify({"msg": "otp Verified successfully"}), 200
        else:
            return jsonify({"msg": "Invalid otp or expired otp"}), 400
    return jsonify({"msg": "User doesn't exist"}), 404

@auth_bp.route("/change-password", methods=["POST"])
def changePassword():
    data = request.json
    email = data.get("email")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.otp_confirmed == True:
  
        if (new_password != confirm_password):
            return jsonify({"msg": "Passwords do not match"}), 400
        
        user.password = generate_password_hash(new_password)
        user.otp_confirmed = None
        db.session.commit()
        
        return jsonify({"msg": "Password changed successfully"}), 201
        
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    return jsonify({"msg": "Unauthorized for this operation"}), 403
    
    
            
    
    