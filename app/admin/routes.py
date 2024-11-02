from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Role, Paper, PaperStatus
from app import db
from app.auth.helper import sendCustomEmail, sendEmail, generatePassword, sendDetailsToEmail
from sqlalchemy.exc import SQLAlchemyError

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

@admin_bp.route('/registeruser', methods=["POST"])
@jwt_required()
def register():
    current_user = get_jwt_identity()
    
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    data = request.json
    email = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone_number = data.get('phone_number')
    theme = data.get('theme')
    role = data.get('role')
    password = generatePassword()
    username = email
    
    print(f"username: {username}, password: {password} ")
    if not email or not first_name or not last_name or not phone_number:
        return jsonify({"msg": "All fields are required"}), 400
    
    if role not in Role._value2member_map_:
        return jsonify({"msg": "Invalid role"}), 400
    
    emailCheck = User.query.filter_by(email=email).first()
    if emailCheck:
        return jsonify({"msg": "Email already exists"}), 400
    
    
    user = User(email=email, first_name=first_name, last_name=last_name, phone_number=phone_number, username=username,
                password=generate_password_hash(password), role=Role(role), assigned_theme=theme)
    print(user.role)
    db.session.add(user)
    db.session.commit()
    
    message_to_send = f"""
    <p>You've been added as a {role} on icaeisd 2024, kindly check below for your login credentials</p>
    <p><strong>Username:</strong> {username}</p>
    <p><strong>Password:</strong> {password}</p>
    """
    sendCustomEmail(subject="Login Credentials", email_body=message_to_send, useremail=email, firstname=first_name, title="Login Details")
    
    return jsonify({"msg": f"User successfully created"}), 200
    


@admin_bp.route('/getauthors', methods=['GET'])
@jwt_required()
def getAllAuthors():
    current_user = get_jwt_identity()
    
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    authors = User.query.filter_by(role=Role.AUTHOR).all()
    
    if not authors:
        return jsonify({"msg": "No author found"}), 400
    
    return jsonify([author.serialize() for author in authors]), 200

@admin_bp.route('/delete/author/int:<author_id>', methods=['DELETE'])
@jwt_required()
def deleteAuthor(author_id):
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    author = User.query.filter_by(id=author_id).first()
    
    if not author:
        return jsonify({"msg": "author not found"}), 404
    
    if author.role != Role.AUTHOR:
            return jsonify({"msg": "this user is not an author"}), 400
    
    try:
        db.session.delete(author)
        db.session.commit()
        
        return jsonify({"msg": "author deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"msg": f"Failed to delete author from database: {str(e)}"}), 500
    

@admin_bp.route('/getreviewers', methods=['GET'])
@jwt_required()
def getAllReviewers():
    current_user = get_jwt_identity()
    
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    reviewers = User.query.filter_by(role=Role.REVIEWER).all()

    
    if not reviewers:
        return jsonify({"msg": "No author found"}), 400
    
    return jsonify([reviewer.serialize() for reviewer in reviewers]), 200
    

@admin_bp.route("/get-all-papers", methods=["GET"])
@jwt_required()
def getPapers():
    current_user = get_jwt_identity()
    
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404
    
    if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403
    
    user_papers = Paper.query.all()
    
    if not user_papers:
        return jsonify({"msg": "No papers found"}), 200
    
    return jsonify([paper.serialize() for paper in user_papers]), 200
    
    
@admin_bp.route('/delete/paper/int:<paper_id>', methods=['DELETE'])
@jwt_required()
def deletePaper(paper_id):
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    paper = Paper.query.filter_by(id=paper_id).first()
    
    if not paper:
        return jsonify({"msg": "paper not found"}), 404
    
    
    try:
        db.session.delete(paper)
        db.session.commit()
        
        return jsonify({"msg": "paper deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"msg": f"Failed to delete paper from database: {str(e)}"}), 500
    
@admin_bp.route('/delete/reviewer/int:<reviewer_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def deleteReviewer(reviewer_id):
    if request.method == 'OPTIONS':
        print("Got here")
        if request.method == 'OPTIONS':
            response = jsonify({"msg": "Options preflight"})
            response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
            response.headers.add("Access-Control-Allow-Methods", "DELETE, OPTIONS")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
            return response, 204
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    reviewer = User.query.filter_by(id=reviewer_id).first()
    
    if not reviewer:
        return jsonify({"msg": "reviewer not found"}), 404
    
    
    try:
        db.session.delete(reviewer)
        db.session.commit()
        
        return jsonify({"msg": "reviewer deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"msg": f"Failed to delete reviewer from database: {str(e)}"}), 500

@admin_bp.route('/delete/reviewers/int:<reviewer_id>', methods=['POST', 'OPTIONS'])
@jwt_required()
def deleteReviewers(reviewer_id):
    if request.method == 'OPTIONS':
        if request.method == 'OPTIONS':
            print("Got here")
            response = jsonify({"msg": "Options preflight"})
            response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
            response.headers.add("Access-Control-Allow-Methods", "DELETE, OPTIONS")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
            return response, 204
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    reviewer = User.query.filter_by(id=reviewer_id).first()
    
    if not reviewer:
        return jsonify({"msg": "reviewer not found"}), 404
    
    
    try:
        db.session.delete(reviewer)
        db.session.commit()
        
        return jsonify({"msg": "reviewer deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"msg": f"Failed to delete reviewer from database: {str(e)}"}), 500


@admin_bp.route('/delete/reviewers', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def deleteReviewers():
    if request.method == 'OPTIONS':
        if request.method == 'OPTIONS':
            print("Got here")
            response = jsonify({"msg": "Options preflight"})
            response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
            response.headers.add("Access-Control-Allow-Methods", "DELETE, OPTIONS")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
            return response, 204
        
    reviewer_id = request.args.get("reviewer_id")
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    reviewer = User.query.filter_by(id=reviewer_id).first()
    
    if not reviewer:
        return jsonify({"msg": "reviewer not found"}), 404
    
    
    try:
        db.session.delete(reviewer)
        db.session.commit()
        
        return jsonify({"msg": "reviewer deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"msg": f"Failed to delete reviewer from database: {str(e)}"}), 500
    
    
    
@admin_bp.route('/assign-theme', methods=['POST'])
@jwt_required()
def assign_theme():
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    data = request.json
    reviewer_id = data.get('reviewer_id')
    theme = data.get('theme')

    reviewer = User.query.get(reviewer_id)
    if not reviewer:
        return jsonify({"msg": "Reviewer not found"}), 404
    
    if reviewer.role != Role.REVIEWER:
        return jsonify({"msg": "this user is not authorized for this operation"}), 403

    reviewer.assigned_theme = theme
    db.session.commit()
    return jsonify({"msg": "Theme assigned successfully"}), 200


    
@admin_bp.route('/unassign-theme/<int:reviewer_id>', methods=['GET'])
@jwt_required()
def unassign_theme(reviewer_id):
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403
        

    reviewer = User.query.get(reviewer_id)
    if not reviewer:
        return jsonify({"msg": "Reviewer not found"}), 404
    
    if reviewer.role != Role.REVIEWER:
        return jsonify({"msg": "this user is not authorized for this operation"}), 403
    
    papers = Paper.query.filter_by(assigned_reviewer_id=reviewer_id).all()
    
    if not papers:
        pass
    for paper in papers:
        paper.assigned_reviewer_id=None
        if paper.paper_status == PaperStatus.CUR:
            paper.paper_status = PaperStatus.P

    reviewer.assigned_theme = None
    db.session.commit()
    return jsonify({"msg": "Theme unassigned successfully"}), 200


