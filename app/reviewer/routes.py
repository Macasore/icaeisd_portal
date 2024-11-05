import ftplib
from io import BytesIO
from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from app import db
from app.auth.helper import sendCustomEmail
from app.models import Paper, PaperStatus, ReviewHistory, Reviewer, Role, User
from werkzeug.security import check_password_hash, generate_password_hash

from app.reviewer.helpers import update_paper_status



reviewer_bp = Blueprint('reviewer', __name__)



@reviewer_bp.route('/login', methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    user = User.query.filter_by(username=username).first()
    
    
    if user and check_password_hash(user.password, password):
        
        if user.role != Role.REVIEWER:
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

@reviewer_bp.route('/papers-for-review', methods=['GET'])
@jwt_required()
def get_papers_for_review():
    current_user = get_jwt_identity() 
    reviewer = User.query.filter_by(id=current_user).first()
    
    if not reviewer:
        return jsonify({"msg": "Invalid user"}), 404

    if reviewer.role != Role.REVIEWER:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    if not reviewer:
        return jsonify({"msg": "Reviewer not found"}), 404
    
    if not reviewer.assigned_theme:
        return jsonify({"msg": "user not assigned a theme yet"}), 400

    papers = Paper.query.filter_by(theme=reviewer.assigned_theme).all()

    return jsonify([paper.serialize() for paper in papers]), 200

@reviewer_bp.route('/claimedpapers', methods=['GET'])
@jwt_required()
def getClaimedPapers():
    current_user = get_jwt_identity() 
    reviewer = User.query.filter_by(id=current_user).first()
    
    if not reviewer:
        return jsonify({"msg": "Invalid user"}), 404

    if reviewer.role != Role.REVIEWER:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    if not reviewer:
        return jsonify({"msg": "Reviewer not found"}), 404
    
    if not reviewer.assigned_theme:
        return jsonify({"msg": "user not assigned a theme yet"}), 400
    
    claimed_papers = Reviewer.query.filter_by(reviewer_id=current_user).all()
    
    paper_ids = [claim.paper_id for claim in claimed_papers]
    
    papers = Paper.query.filter(Paper.id.in_(paper_ids)).all()

    return jsonify([paper.serialize() for paper in papers]), 200



@reviewer_bp.route('/claim-paper/<int:reviewer_id>', methods=['POST'])
@jwt_required()
def claim_paper(reviewer_id):
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.REVIEWER:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    data = request.json
    paper_id = data.get('paper_id')

    paper = Paper.query.get(paper_id)
    if not paper:
        return jsonify({"msg": "Paper not found"}), 404
    
    
    if reviewer_id != user.id:
        return jsonify({"msg": "Reviewer id not authorized for this operation"}), 403
    
    if paper.theme != user.assigned_theme:
        return jsonify({"msg": "This paper is not under your assigned theme"}), 400
    
    if paper.paper_status == PaperStatus.A:
        return jsonify({"msg": "can't review an already accepted paper"}), 400
    
    if (paper.reviewer_count or 0) >= 2:
        return jsonify({"msg": "Reviewer limit reached"}), 403
        
    review = Reviewer.query.filter_by(reviewer_id=reviewer_id).first()
    
    if review:
        return jsonify({"msg": "you have already claimed this paper"}), 400
    
    reviewer_claim = Reviewer(paper_id=paper_id, reviewer_id=reviewer_id)
    
    if paper.reviewer_count is None:
        paper.reviewer_count = 0
        
    paper.reviewer_count += 1
    paper.paper_status = PaperStatus.CUR
    db.session.add(reviewer_claim)
    db.session.commit()
    return jsonify({"msg": "Paper claimed successfully"}), 200

@reviewer_bp.route('/submit-review/<int:reviewer_id>', methods=['POST'])
@jwt_required()
def submit_review(reviewer_id):
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.REVIEWER:
            return jsonify({"msg": "not authorized for this operation"}), 403
    
    data = request.json
    paper_id = data.get('paper_id')
    review_comment = data.get('review_comment')
    review_status = data.get('review_status') 
    review_questions = data.get('review_questions')

    paper = Paper.query.get(paper_id)
    reviewer = User.query.get(reviewer_id)
    
    if not paper:
        return jsonify({"msg": "paper not found"}), 404
    
    if not reviewer:
        return jsonify({"msg": "Reviewer not found"}), 404
    
    if reviewer_id != user.id:
        return jsonify({"msg": "Reviewer id not authorized for this operation"}), 403
    
    if paper.paper_status == PaperStatus.A:
        return jsonify({"msg": "can't review an already accepted paper"}), 400
    
    reviewer_claim = Reviewer.query.filter_by(paper_id=paper_id, reviewer_id=reviewer_id).first()
    
    if not reviewer_claim:
        return {"msg": "You have not claimed this paper."}, 403
    
    review_history_entry = ReviewHistory(
        paper_id=paper_id,
        reviewer_id=reviewer_id,
        status=PaperStatus(review_status),
        comment=review_comment,
        review_questions=review_questions
    )
    

    paper.review_comment = review_comment 
    
    db.session.add(review_history_entry)
    db.session.commit()
    
    final_paper_status = PaperStatus.CUR
    print(paper.reviewer_count)
    if paper.reviewer_count == 2:
        print("yeah")
        final_paper_status = update_paper_status(paper_id)
    paper.paper_status = final_paper_status
    db.session.commit()
    author_email = paper.author.email
    message = "A review has been submitted on your paper, kindly check your portal to view feedback"
    sendCustomEmail(subject="Paper Review", email_body=message, useremail=author_email, firstname="Author", title="Paper Review")
    return jsonify({"msg": "Review submitted and history logged"}), 200



@reviewer_bp.route('/unclaim-paper/<int:reviewer_id>', methods=['POST'])
@jwt_required()
def unclaim_paper(reviewer_id):
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.REVIEWER:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    data = request.json
    paper_id = data.get('paper_id')

    paper = Paper.query.get(paper_id)
    if not paper:
        return jsonify({"msg": "Paper not found"}), 404
    
    if paper.theme != user.assigned_theme:
        return jsonify({"msg": "This paper is not under your assigned theme"}), 400
    
    if reviewer_id != user.id:
        return jsonify({"msg": "Reviewer id not authorized for this operation"}), 403
        

    reviewer_claim = Reviewer.query.filter_by(paper_id=paper_id, reviewer_id=reviewer_id).first()
    
    if not reviewer_claim:
        return jsonify({"msg": "you have not claimed this paper"}), 404
    
    db.session.delete(reviewer_claim)
    db.session.commit()
    return jsonify({"msg": "Paper unassigned successfully"}), 200

@reviewer_bp.route('/delete-review/<int:reviewer_id>/<int:paper_id>', methods=['DELETE'])
@jwt_required()
def delete_review(reviewer_id, paper_id):
    current_user = get_jwt_identity() 
    user = User.query.filter_by(id=current_user).first()
    
    review_id = request.args.get("review_id")
    
    if not user:
        return jsonify({"msg": "Invalid user"}), 404

    if user.role != Role.REVIEWER:
            return jsonify({"msg": "not authorized for this operation"}), 403
        
    if reviewer_id != user.id:
        return jsonify({"msg": "Reviewer id not authorized for this operation"}), 403
        
    paper = Paper.query.get(paper_id)
    if not paper:
        return jsonify({"msg": "Paper not found"}), 404
    
    reviewer_claim = Reviewer.query.filter_by(paper_id=paper_id, reviewer_id=reviewer_id).first()
    
    if not reviewer_claim:
        return jsonify({"msg": "you have not claimed this paper"}), 404
    
    review = ReviewHistory.query.get(review_id)
    
    if not review:
        return jsonify({"msg": "request review doesn't exist"}), 400
    
    db.session.delete(review)
    db.session.commit()
    
    return jsonify({"msg": "review successfully deleted"}), 200

   
@reviewer_bp.route('/download-paper/<int:paper_id>', methods=['GET'])
@jwt_required()
def downloadPaper(paper_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    if not user:
        return jsonify({"msg": "Invalid user"}), 404
    
    if user.role != Role.REVIEWER:
            return jsonify({"msg": "not authorized for this operation"}), 403

    paper = Paper.query.get(paper_id)
    if not paper:
        return jsonify({"msg": "Paper not found"}), 404
    
    reviewer_claim = Reviewer.query.filter_by(paper_id=paper_id, reviewer_id=user.id).first()
    
    if not reviewer_claim:
        return jsonify({"msg": "you have not claimed this paper"}), 404
    
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
    
    