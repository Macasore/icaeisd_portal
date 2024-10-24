from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Role, CoAuthor, Paper
from .helpers import MAX_ABSTRACT_WORDS, check_paper_limits, validate_abstract
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
        return jsonify({"msg": "Unauthorized for this operation"}), 403
    
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
    
    is_valid, word_count = validate_abstract(abstract)
    
    if not is_valid:
        return jsonify({"msg": f"Abstract is too long. Current word count is {word_count}, but the limit is {MAX_ABSTRACT_WORDS} words."}), 400
    
    if 'file' not in request.files:
        return jsonify({"msg": "No file part in the request"}), 400
    
    file = request.files.get('file')
    
    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"msg": "Only PDF files are allowed"}), 400
    
    file_name = secure_filename(file.filename)
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], theme, subtheme).replace(" ", "_")
    print(upload_folder)
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, file_name).replace(" ", "_")
    print(file_path)
    file.save(file_path)
    
    paper = Paper(
        title=title,
        theme=theme,
        subtheme=subtheme,
        abstract=abstract,
        file_path=file_path,
        author_id=author.id
    )
    if coauthors:
        try:
            coauthors = json.loads(coauthors) 
        except json.JSONDecodeError:
            return jsonify({"msg": "Invalid coauthor data format"}), 400
    
    for coauthor_data in coauthors:
        coauthor_email = coauthor_data.get('email')  # Safely access 'email'
        
        can_submit_coauthor, message = check_paper_limits(coauthor_email)
        
        if not can_submit_coauthor:
            return jsonify({"msg": f"Coauthor {coauthor_email} cannot be added: {message}"}), 400
        
        coauthor = CoAuthor(full_name=coauthor_data.get('name'), email=coauthor_email, paper=paper)
        db.session.add(coauthor)
        
    db.session.add(paper)
    db.session.commit()
    
    return jsonify({"msg": "Paper submitted successfully"}), 201
    
    
@author_bp.route("/get-papers", methods=["GET"])
@jwt_required()
def getPapers():
    current_user = get_jwt_identity()
    
    user_papers = Paper.query.filter_by(author_id=current_user).all()
    
    if not user_papers:
        return None
    
    return jsonify([paper.serialize() for paper in user_papers]), 200

@author_bp.route('/files', methods=['POST'])
@jwt_required()
def get_file():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    data = request.json
    file_url = data.get("file_url")

    normalized_path = os.path.normpath(file_url)
    print(f"Normalized path: {normalized_path}")

    paper = Paper.query.filter_by(file_path=normalized_path).first()

    if paper and paper.author_id == user.id:
        file_path = os.path.join(os.getcwd(), normalized_path)
        print(f"Full file path: {file_path}")

        if os.path.exists(file_path):
            print("File found, sending file...")
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"msg": "File not found"}), 404
    else:
        return jsonify({"msg": "Requested paper doesn't exist"}), 404
        return jsonify({"msg": "requested paper doesn't exist"}), 404