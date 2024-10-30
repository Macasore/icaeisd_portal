import base64
import random
import string, os
from flask_mail import Message
from app import mail
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
from flask import render_template_string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
def sendCustomEmail(subject, email_body, useremail, firstname, title, cc=None):
    msg = Message(subject=subject, sender='support@icaeisdcovenantuniversity.org',cc=cc, recipients=[useremail])
    msg.body = email_body
    title = title
    author_name = firstname
    body = email_body
    msg.html = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
  </head>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px;">
                
      <p>Dear {author_name},</p>
      
      <p>{body}</p>
      
      <p>Best Regards,</p>
      
      <p><strong>ICAEISD 2024 Team</strong></p>
      
      <a href="https://icaeisd2024.covenantuniversity.edu.ng" style="display: inline-block; background-color: #7a008d; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 20px;">
        Go to Website
      </a>
    </div>
    
    <div style="margin-top: 20px; font-size: 12px; color: #666;">
      <p>Copyright 2024 Covenant University. All rights reserved.</p>
    </div>
  </body>
</html>
'''
    mail.send(msg)
    return "Message sent!"
    mail.send(msg)
    return "Message sent!"
   
  
    
def generateOtp():
    otp = ''.join(random.choice(string.digits) for i in range(6))
    return otp

def verify_otp(otp, hashed_otp):
    return check_password_hash(hashed_otp, otp)