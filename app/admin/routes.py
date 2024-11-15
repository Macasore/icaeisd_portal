import ftplib
from io import BytesIO
from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import Reviewer, User, Role, Paper, PaperStatus
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
    <p>You've been added as a/an {role} on icaeisd 2024, kindly check below for your login credentials</p>
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

@admin_bp.route('/delete/author', methods=['DELETE'])
@jwt_required()
def deleteAuthor():
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    author_id = request.args.get('author_id')
    
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
    
    
@admin_bp.route('/delete/paper', methods=['DELETE'])
@jwt_required()
def deletePaper():
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    paper_id = request.args.get("paper_id")
    
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
 
@admin_bp.route('/delete/reviewer', methods=['DELETE', 'OPTIONS'])
def deleteReviewers2():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 204
    
    # Only proceed with DELETE requests
    if request.method == 'DELETE':
        try:
            # Verify JWT first
            verify_jwt_in_request()
            
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
        except Exception as e:
            return jsonify({"msg": str(e)}), 401
            
    return jsonify({"msg": "Method not allowed"}), 405   
    
    
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
    
    claimed_papers = Reviewer.query.filter_by(reviewer_id=reviewer_id).all()
    
    for claim in claimed_papers:
        paper = Paper.query.get(claim.paper_id)
        
        if paper:
            db.session.delete(claim)
            if paper.paper_status == PaperStatus.CUR:
                paper.paper_status = PaperStatus.P

    reviewer.assigned_theme = None
    db.session.commit()
    return jsonify({"msg": "Theme unassigned successfully"}), 200

@admin_bp.route('/payments', methods=['GET'])
@jwt_required()
def get_all_payments():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    if not user or user.role != Role.ADMIN:
        return jsonify({"msg": "Unauthorized"}), 403

    users = User.query.filter(User.payment_path.isnot(None)).all()

    return jsonify([{
        "id": u.id,
        "email": u.email,
        "payment_url": u.payment_path,
        "is_paid": u.is_paid,
        "payment_confirmed": u.payment_confirmed,
        "created_at": u.created_at.isoformat()
    } for u in users]), 200


@admin_bp.route('/download/payment', methods=['GET'])
@jwt_required()
def download_payment():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()
    
    user_id = request.args.get("user_id")

    if not user or user.role != Role.ADMIN:
        return jsonify({"msg": "Unauthorized"}), 403

    user_to_download = User.query.get(user_id)

    if not user_to_download:
        return jsonify({"msg": "User not found"}), 404

    if not user_to_download.payment_path:
        return jsonify({"msg": "No receipt available for download"}), 404
    
    file_path = user_to_download.payment_path

    try:
       
        with ftplib.FTP(current_app.config['FTP_HOST']) as ftp:
            ftp.login(current_app.config['FTP_USER'], current_app.config['FTP_PASS'])

            
            file_stream = BytesIO()
            ftp.retrbinary(f'RETR {file_path}', file_stream.write)

            file_stream.seek(0) 

            file_name = file_path.split('/')[-1] 
            return send_file(file_stream, as_attachment=True, download_name=file_name)

    except ftplib.all_errors as e:
        return jsonify({"msg": f"FTP download failed: {str(e)}"}), 500
    
@admin_bp.route('/payment/status', methods=['PUT'])
@jwt_required()
def confirm_or_reject_payment():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    if not user or user.role != Role.ADMIN:
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.json
    user_id = data.get('user_id')
    new_status = data.get('status')

    if new_status not in ['CONFIRMED', 'REJECTED']:
        return jsonify({"msg": "Invalid status"}), 400

    user_to_update = User.query.get(user_id)

    if not user_to_update:
        return jsonify({"msg": "User not found"}), 404

    if new_status == 'CONFIRMED':
        user_to_update.payment_confirmed = True
    else:
        user_to_update.payment_confirmed = False

    db.session.commit()

    return jsonify({"msg": f"Payment {new_status.lower()} successfully."}), 200


@admin_bp.route('/download-paper', methods=['GET'])
@jwt_required()
def downloadPaperAdmin():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()
    
    paper_id = request.args.get("paper_id")

    if not user:
        return jsonify({"msg": "Invalid user"}), 404
    
    if user.role != Role.ADMIN:
            return jsonify({"msg": "not authorized for this operation"}), 403

    paper = Paper.query.get(paper_id)
    if not paper:
        return jsonify({"msg": "Paper not found"}), 404
    
    file_path = paper.file_path
    
    if not file_path:
        return jsonify({"msg": "File path not provided"}), 400
     
    try:
       
        with ftplib.FTP(current_app.config['FTP_HOST']) as ftp:
            ftp.login(current_app.config['FTP_USER'], current_app.config['FTP_PASS'])

            
            file_stream = BytesIO()
            ftp.retrbinary(f'RETR {file_path}', file_stream.write)

            file_stream.seek(0) 

            file_name = file_path.split('/')[-1] 
            return send_file(file_stream, mimetype='application/pdf', as_attachment=True, download_name=file_name)

    except ftplib.all_errors as e:
        return jsonify({"msg": f"FTP download failed: {str(e)}"}), 500
    
   