from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Role, CoAuthor, Paper
from .helpers import check_paper_limits
from werkzeug.utils import secure_filename
import os, json
from app import db

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
        return jsonify({"msg": "Unauthorized for this operation"}, 400)
    
    can_submit, message = check_paper_limits(current_user_email)
    
    if not can_submit:
        return jsonify({"msg": f"author {current_user_email} cannoxt be added: {message}"}), 400
    
    if not can_submit:
        return jsonify({"msg": message}), 403
    
    title = request.form.get("title")
    theme = request.form.get("theme")
    subtheme = request.form.get("subtheme")
    abstract = request.form.get("abstract")
    coauthors = request.form.get("coauthors", []) 
    
    if 'file' not in request.files:
        return jsonify({"msg": "No file part in the request"}), 400
    
    file = request.files.get('file')
    
    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"msg": "Only PDF files are allowed"}), 400
    
    file_name = secure_filename(file.filename)
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], theme, subtheme)
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, file_name)
    file.save(file_path)
    
    paper = Paper(
        title=title,
        theme=theme,
        subtheme=subtheme,
        abstract=abstract,
        file_path=file_path,
        author_id=author.id
    )
    
    for coauthor_data in coauthors:
        coauthor_email = coauthor_data['email']
        
        can_submit_coauthor, message = check_paper_limits(coauthor_email)
        
        if not can_submit_coauthor:
            return jsonify({"msg": f"Coauthor {coauthor_email} cannot be added: {message}"}), 400
    
        coauthor = CoAuthor(full_name=coauthor_data['name'], email=coauthor_email, paper=paper)
        db.session.add(coauthor)
        
    db.session.add(paper)
    db.session.commit()
    
    return jsonify({"msg": "Paper submitted successfully"}), 201
    
    
    