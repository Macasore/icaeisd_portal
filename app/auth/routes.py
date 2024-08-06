from app.models import User
from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from app.helper import generatePassword, generateUsername

auth_bp = Blueprint('auth',__name__ )

@auth_bp.route("/register", methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone_number = data.get('phone_number')
    password = generatePassword()
    username = generateUsername()
    