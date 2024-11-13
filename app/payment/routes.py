import ftplib
from flask import Blueprint, current_app, request, jsonify
from app.models import Role, User, Paper
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity

payment_bp = Blueprint('payment', __name__)

MAX_FILE_SIZE = 2 * 1024 * 1024
@payment_bp.route("attendee-payment", methods=['POST'])
def makePaymentForAttendee():
    email = request.form.get('email')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    phone_number = request.form.get('phone_number')
    role = request.form.get('role')
    
    emailCheck = User.query.filter_by(email=email).first()
    if emailCheck:
        return jsonify({"msg": f"email provided is already connected to a/an {emailCheck.role.name}'s account"}), 400
    
    if 'file' not in request.files:
        return jsonify({"msg": "No file part in the request"}), 400
    
    if role not in Role._value2member_map_:
        return jsonify({"msg": "Invalid role"}), 400
    
    file = request.files.get('file')
    
    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400
    
    if request.content_length > MAX_FILE_SIZE:
        return jsonify({"msg": "File size exceeds the limit of 2 MB."}), 400
    
    filename = file.filename
    upload_path = f"{email} - {filename}"
    try:
        ftp = ftplib.FTP(current_app.config['FTP_HOST'])
        ftp.login(current_app.config['FTP_USER'], current_app.config['FTP_PASS'])
        

        ftp.cwd('/payments') 
        
    
        ftp.storbinary(f"STOR {upload_path}", file.stream)  
        ftp.quit()

    except ftplib.all_errors as e:
        return jsonify({"msg": f"FTP upload failed: {str(e)}"}), 500
    
    payment_path = "/payments/" + upload_path
    user = User(email=email, first_name=first_name, last_name=last_name, phone_number=phone_number, role=Role(role), is_paid=True, payment_path=payment_path)
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "your payment has been received kindly check you email for confirmation receipt within 2-3 working days"}), 200


@payment_bp.route("paper-payment/<int:paper_id>", methods=['POST'])
@jwt_required()
def makePaymentForPaper(paper_id):
    curent_user = get_jwt_identity()
    user = User.query.filter_by(id=curent_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404
    
    paper = Paper.query.filter_by(id=paper_id).first()
    
    if not paper:
        return jsonify({"msg": "file not found"}), 404
    
    if paper.author_id != user.id:
        return jsonify({"msg": "You don't have access to this file"}), 403
    
    if paper.paper_status.name != "A":
        return jsonify({"msg": "can't make payment till your paper is accepted"}), 400
    
    if 'file' not in request.files:
        return jsonify({"msg": "No file part in the request"}), 400
    
    proof = request.files.get('file')
    
    if proof.filename == '':
        return jsonify({"msg": "No selected file"}), 400
    
    if request.content_length > MAX_FILE_SIZE:
        return jsonify({"msg": "File size exceeds the limit of 2 MB."}), 400
    
    filename = proof.filename
    upload_path = f"{user.email} - {filename}"
    try:
        ftp = ftplib.FTP(current_app.config['FTP_HOST'])
        ftp.login(current_app.config['FTP_USER'], current_app.config['FTP_PASS'])
        

        ftp.cwd('/payments') 
        
    
        ftp.storbinary(f"STOR {upload_path}", proof.stream)  
        ftp.quit()

    except ftplib.all_errors as e:
        return jsonify({"msg": f"FTP upload failed: {str(e)}"}), 500
    
    paper.is_paid = True
    paper.payment_path = "/payments/" + upload_path
    db.session.commit()
    
    return jsonify({"msg": "your payment has been received kindly check you email for confirmation receipt within 2-3 working days"}), 200
