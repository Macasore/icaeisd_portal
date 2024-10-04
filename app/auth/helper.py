import random
import string, os
from flask_mail import Message
from app import mail
from dotenv import load_dotenv

load_dotenv()

def generatePassword():
    length = random.randint(8,15)
    characters = string.ascii_letters + string.punctuation + string.digits
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def sendDetailsToEmail(username, password, useremail):
    sender=os.getenv('DefaultFromMail')
    msg = Message(subject="Login Credentials", sender=sender, recipients=[useremail])
    msg.body = f"Find your Login Credentials for icaeisd portal below\n\n Username: {username}\n Password: {password}"
    mail.send(msg)
    return "Message Sent!"
    
    