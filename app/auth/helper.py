import random
import string, os
from flask_mail import Message
from app import mail
from dotenv import load_dotenv
from werkzeug.security import check_password_hash

load_dotenv()

def generatePassword():
    length = random.randint(8,15)
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def sendDetailsToEmail(username, password, useremail):
    sender=os.getenv('DefaultFromMail')
    msg = Message(subject="Login Credentials", sender=sender, recipients=[useremail])
    msg.body = f"Find your Login Credentials for icaeisd portal below\n\n Username: {username}\n Password: {password}"
    mail.send(msg)
    return "Message Sent!"
    
def sendEmail(subject, message, useremail):
    try:
        sender = os.getenv('DefaultFromMail')
        msg = Message(subject=subject, sender=sender, recipients=[useremail])
        msg.body = message
        mail.send(msg)
        return "Mail sent!", 200
    except Exception as e:
        print(f"Error sending email: {e}")
        return "An error occurred while sending the email. Please try again later.", 500

def generateOtp():
    otp = ''.join(random.choice(string.digits) for i in range(6))
    return otp

def verify_otp(otp, hashed_otp):
    return check_password_hash(hashed_otp, otp)