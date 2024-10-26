import ftplib
from flask import Blueprint, current_app, request, jsonify
from app.models import Role, User
from app import db

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
    #create user with attendee mark and paymenturl
    
    user = User(email=email, first_name=first_name, last_name=last_name, phone_number=phone_number, role=Role(role), is_paid=True, payment_path=upload_path)
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "your payment has been received kindly check you email for confirmation receipt within 2-3 working days"})