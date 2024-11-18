from io import BytesIO
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Role, CoAuthor, Paper, PaperStatus
from .helpers import MAX_ABSTRACT_WORDS, check_paper_limits, validate_abstract
from werkzeug.utils import secure_filename
import os, json
from app import db
from app.auth.helper import sendCustomEmail, sendEmail
import ftplib
from flask_cors import cross_origin
from sqlalchemy.exc import SQLAlchemyError


MAX_FILE_SIZE = 5 * 1024 * 1024

author_bp = Blueprint('author',__name__ )

@author_bp.route("/submit-paper", methods=["POST"])
@jwt_required()
def submitPaper():
    current_user = get_jwt_identity() 
    current_user_email = User.query.filter_by(id=current_user).first().email
    
    author = User.query.filter_by(id=current_user).first()
    
    if not author:
        return jsonify({"msg": "User not found"}), 404
    
    if author.role != Role.AUTHOR:
        return jsonify({"msg": "Unauthorized for this operation"}), 403
    
    can_submit, message = check_paper_limits(current_user_email)
    
    if not can_submit:
        return jsonify({"msg": f"author {current_user_email} cannoxt be added: {message}"}), 400
    
    
    title = request.form.get("title")
    abstract = request.form.get("abstract")
    coauthors = request.form.get("coauthors", []) 
    
    is_valid, word_count = validate_abstract(abstract)
    
    if not is_valid:
        return jsonify({"msg": f"Abstract is too long. Current word count is {word_count}, but the limit is {MAX_ABSTRACT_WORDS} words."}), 400
    
    if 'file' not in request.files:
        return jsonify({"msg": "No file part in the request"}), 400
    
    file = request.files.get('file')
    
    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400
    
    if request.content_length > MAX_FILE_SIZE:
        return jsonify({"msg": "File size exceeds the limit of 5 MB."}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"msg": "Only PDF files are allowed"}), 400
    
    file_name = secure_filename(file.filename)
    theme = request.form.get("theme")
    subtheme = request.form.get("subtheme")
    upload_path = f"{theme}/{subtheme}/{file_name}"
    
    try:
        ftp = ftplib.FTP(current_app.config['FTP_HOST'])
        ftp.login(current_app.config['FTP_USER'], current_app.config['FTP_PASS'])
        

        ftp.cwd('/uploads') 
        try:
            ftp.mkd(theme)
        except ftplib.error_perm:
            pass  

        try:
            ftp.mkd(f"{theme}/{subtheme}")
        except ftplib.error_perm:
            pass  

    
        ftp.storbinary(f"STOR {upload_path}", file.stream)  
        ftp.quit()

        
        file_path = f"ftp://{current_app.config['FTP_HOST']}/{upload_path}"

    except ftplib.all_errors as e:
        return jsonify({"msg": f"FTP upload failed: {str(e)}"}), 500

    
    print(file_path)
    upload_path = "/uploads/"+ upload_path
    
    paper = Paper(
        title=title,
        theme=theme,
        subtheme=subtheme,
        abstract=abstract,
        file_path=upload_path,
        author_id=author.id,
        paper_status=PaperStatus("pending")
    )
    if coauthors:
        try:
            coauthors = json.loads(coauthors) 
        except json.JSONDecodeError:
            return jsonify({"msg": "Invalid coauthor data format"}), 400
    
    coauthor_emails = []
    for coauthor_data in coauthors:
        coauthor_email = coauthor_data.get('email') 
        
        can_submit_coauthor, message = check_paper_limits(coauthor_email)
        
        if not can_submit_coauthor:
            return jsonify({"msg": f"Coauthor {coauthor_email} cannot be added: {message}"}), 400
        
        coauthor = CoAuthor(first_name=coauthor_data.get('first_name'),last_name=coauthor_data.get('last_name'), email=coauthor_email, paper=paper)
        db.session.add(coauthor)
        coauthor_emails.append(coauthor_email)
        
    db.session.add(paper)
    db.session.commit()
    message = "\n\nThank you for your submission to ICAEISD 2024.\nKindly check back for the status of your manuscript while we review your paper."
    sendCustomEmail(subject="Paper Submission", email_body=message, useremail=current_user_email, firstname=author.first_name, title="Contact Message",cc=coauthor_emails)
    sendEmail(subject="Paper Submission", email_body="Please find attached the submitted paper", useremail="icaeisd2024@cu.edu.ng", cc=["icaeisd2024sec@cu.edu.ng"], attachment=file.stream)
    return jsonify({"msg": "Paper submitted successfully"}), 201
    

# @author_bp.route("/test_sendfile", methods=["POST"])
# def test():
#     file = request.files.get("file")
    
#     sendEmail(subject="Paper Submission", email_body="Please find attached the submitted paper", useremail="macasorekingdavid@gmail.com", cc=["macasoredavidking@gmail.com"], attachment=file.stream)
#     return ("return successful")

@author_bp.route("/get-papers", methods=["GET"])
@jwt_required()
def getPapers():
    current_user = get_jwt_identity()
    
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404
    
    user_papers = Paper.query.filter_by(author_id=current_user).all()
    
    if not user_papers:
        return jsonify({"msg": "No paper found for user"}), 200
    
    return jsonify([paper.serialize() for paper in user_papers]), 200

@author_bp.route('/getPaper', methods=['GET'])
@jwt_required()
def get_file():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    file_path = request.args.get('file_path')
    
    if not file_path:
        return jsonify({"msg": "File path not provided"}), 400
    
    paper = Paper.query.filter_by(file_path=file_path).first()
    
    if not paper:
        return jsonify({"msg": "file not found"}), 404
    
    if paper.author_id != user.id:
        return jsonify({"msg": "You don't have access to this file"}), 403
        
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
    
    
@author_bp.route('/delete-paper', methods=['DELETE'])
@jwt_required()
def deletePaper():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    if not user:
        return jsonify({"msg": "Invalid user"}), 404
    
    paper_id = request.args.get('paper-id')
    print(paper_id)
    
    paper = Paper.query.filter_by(id=paper_id).first()
    print(paper)
    
    if not paper:
        return jsonify({"msg": "paper not found"}), 404
    
    if paper.author_id != user.id:
        return jsonify({"msg": "You don't have access to this file"}), 403
    
    if paper.reviewer_count >= 1:
        return jsonify({"msg": "can't delete paper already being reviewed"}), 400
    
    file_path = paper.file_path
    
    dir_path, file_name = '/'.join(file_path.split('/')[:-1]), file_path.split('/')[-1]
    
    file_name2 = file_name.replace(" ", "_")
    print(f"filename 2{file_name2}")
    print("=======")    
    print(file_name)

    
    try:
        with ftplib.FTP(current_app.config['FTP_HOST']) as ftp:
            ftp.login(current_app.config['FTP_USER'], current_app.config['FTP_PASS'])
            ftp.cwd(dir_path)
            
            
            if file_name not in ftp.nlst():
                print(ftp.nlst())
                return jsonify({"msg": "file not found on the server"}), 404
            
            ftp.delete(file_name)
    except ftplib.all_errors as e:
        return jsonify({"msg": f"failed to delete file from server: {str(e)}"}), 500
    
    try:
        db.session.delete(paper)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"msg": f"Failed to delete paper from database: {str(e)}"}), 500
    
    return jsonify({"msg": "Paper deleted successfully"}), 200
    
@author_bp.route("/edit-paper", methods=["PUT"])
@jwt_required()
def editPaper():
    current_user = get_jwt_identity() 
    current_user_email = User.query.filter_by(id=current_user).first().email
    
    author = User.query.filter_by(id=current_user).first()
    paper_id = request.args.get("paper_id")
    
    if not author:
        return jsonify({"msg": "User not found"}), 404
    
    if author.role != Role.AUTHOR:
        return jsonify({"msg": "Unauthorized for this operation"}), 403

    paper = Paper.query.get(paper_id)
    if not paper:
        return jsonify({"msg": "Paper not found"}), 404

    if paper.author_id != author.id:
        return jsonify({"msg": "You are not authorized to edit this paper"}), 403

    title = request.form.get("title", paper.title)
    abstract = request.form.get("abstract", paper.abstract)
    coauthors = request.form.get("coauthors", []) 

    is_valid, word_count = validate_abstract(abstract)
    if not is_valid:
        return jsonify({"msg": f"Abstract is too long. Current word count is {word_count}, but the limit is {MAX_ABSTRACT_WORDS} words."}), 400

    file_path = paper.file_path
    
    if 'file' not in request.files:
        return jsonify({"msg": "No file part in the request"}), 400
    

    file = request.files.get('file')

    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400

    if request.content_length > MAX_FILE_SIZE:
        return jsonify({"msg": "File size exceeds the limit of 5 MB."}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"msg": "Only PDF files are allowed"}), 400

    file_name = secure_filename(file.filename)
    theme = request.form.get("theme", paper.theme)
    subtheme = request.form.get("subtheme", paper.subtheme)
    upload_path = f"{theme}/{subtheme}/{file_name}"

    try:
        ftp = ftplib.FTP(current_app.config['FTP_HOST'])
        ftp.login(current_app.config['FTP_USER'], current_app.config['FTP_PASS'])
        ftp.cwd('/uploads')

        try:
            ftp.mkd(theme)
        except ftplib.error_perm:
            pass 

        try:
            ftp.mkd(f"{theme}/{subtheme}")
        except ftplib.error_perm:
            pass 
        ftp.storbinary(f"STOR {upload_path}", file.stream)  
        ftp.quit()

        file_path = f"ftp://{current_app.config['FTP_HOST']}/{upload_path}"

    except ftplib.all_errors as e:
        return jsonify({"msg": f"FTP upload failed: {str(e)}"}), 500
    
    upload_path = "/uploads/"+ upload_path

    paper.title = title
    paper.abstract = abstract
    paper.file_path = upload_path
    paper.theme = theme
    paper.subtheme = subtheme


    CoAuthor.query.filter_by(paper_id=paper.id).delete()
    
    if coauthors:
        try:
            coauthors = json.loads(coauthors) 
        except json.JSONDecodeError:
            return jsonify({"msg": "Invalid coauthor data format"}), 400
        
        for coauthor_data in coauthors:
            coauthor_email = coauthor_data.get('email')
            can_submit_coauthor, message = check_paper_limits(coauthor_email)

            if not can_submit_coauthor:
                return jsonify({"msg": f"Coauthor {coauthor_email} cannot be added: {message}"}), 400

            coauthor = CoAuthor(first_name=coauthor_data.get('first_name'), last_name=coauthor_data.get('last_name'), email=coauthor_email, paper=paper)
            db.session.add(coauthor)

    db.session.commit()
    
    message = "Dear Author,\n\nYour submission has been updated. Please check the portal for the status of your manuscript.\n\n\nRegards,\nICAEISD 2024 Team."
    sendEmail("Paper Update", message, current_user_email)

    return jsonify({"msg": "Paper updated successfully"}), 200

@author_bp.route('/paper/<int:paper_id>/review-history', methods=['GET'])
@jwt_required()
def get_review_history(paper_id):
    current_user = get_jwt_identity() 
    current_user_email = User.query.filter_by(id=current_user).first().email
    
    author = User.query.filter_by(id=current_user).first()
    
    if not author:
        return jsonify({"msg": "User not found"}), 404
    
    if author.role != Role.AUTHOR:
        return jsonify({"msg": "Unauthorized for this operation"}), 403
    paper = Paper.query.get(paper_id)
    
    if not paper:
        return jsonify({"msg": "Paper not found"}), 404

    history = [
        {
            "reviewer_id": entry.reviewer_id,
            "status": entry.status.value,
            "comment": entry.comment,
            "reviewed_at": entry.reviewed_at.isoformat()
        }
        for entry in paper.review_history
    ]
    
    return jsonify({"history": history}), 200