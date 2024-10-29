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
def sendCustomEmail(subject, email_body, useremail, firstname, title):
    try:
        email_message = MIMEMultipart("alternative")
        email_message["Subject"] = subject
        email_message["From"] = os.getenv("DefaultFromMail")
        email_message["To"] = useremail
        text = """\
        Hi,
        Check out the new post on the Mailtrap blog:
        SMTP Server for Testing: Cloud-based or Local?
        https://blog.mailtrap.io/2018/09/27/cloud-or-local-smtp-server/
        Feel free to let us know what content would be useful for you!"""
        
        with open("app/static/cu_logo.jpg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        html = f"""\
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px;">
        <img src="data:image/jpeg;base64,{encoded_string}" alt="Covenant University Logo" style="max-width: 200px; height: auto; margin-bottom: 20px;" />
            <h1 style="color: #4b0082; font-size: 24px; margin-bottom: 20px;">{title}</h1>
        
        <p>Dear {firstname},</p>
        
        <p>{email_body}</p>
        
        <p>Best Regards,</p>
        
        <p><strong>ICAEISD 2024 Team</strong></p>
        
        <a href="icaeisdcovenantuniversity.org" style="display: inline-block; background-color: #7a008d; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 20px;">
            Go to Website
        </a>
        </div>
        
        <div style="margin-top: 20px; font-size: 12px; color: #666;">
        <p>Copyright 2024 Covenant University. All rights reserved.</p>
        </div>
    </body>
        """

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        email_message.attach(part1)
        email_message.attach(part2)

        with smtplib.SMTP(os.getenv("MAIL_SERVER"), 587) as server:
            server.starttls()
            server.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
            server.sendmail(
                os.getenv("DefaultFromMail"), useremail, email_message.as_string()
            )

        return "Mail sent", 200
    except Exception as e:
        print(f"Error sending email: {e}")
        return "An error occurred while sending the email. Please try again later.", 500
   
  
    
def generateOtp():
    otp = ''.join(random.choice(string.digits) for i in range(6))
    return otp

def verify_otp(otp, hashed_otp):
    return check_password_hash(hashed_otp, otp)