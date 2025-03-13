from flask import Blueprint, render_template, redirect, url_for, flash, request,session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db
from flask_wtf.csrf import generate_csrf
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
from flask_wtf.csrf import CSRFProtect


def generate_otp_email_body():
    otp = str(random.randint(100000, 999999))  # Generate a 6-digit OTP
    session['otp']=otp
    email_body = f"""

    Your One-Time Password (OTP) for verification is: **{otp}**

    Please use this code within the next 10 minutes. Do not share it with anyone.

    If you did not request this code, please ignore this email.

    Best regards,  
    Disaster warning team
    """
    return email_body  # Returning OTP along with the email body

def send_email(body, recipient_email, smtp_server="smtp.gmail.com", smtp_port=587):
    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = "kr4785543@gmail.com"
        msg['To'] = recipient_email
        msg['Subject'] = "Mail verification"

        # Attach email body
        msg.attach(MIMEText(body, 'plain'))

        # Establish connection with SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login("kr4785543@gmail.com","qfbfvahyrcwctewf" )  # Login to the email account

        # Send the email
        server.sendmail("kr4785543@gmail.com", recipient_email, msg.as_string())

        # Close the connection
        server.quit()
        print("Email sent successfully!")

    except Exception as e:
        print(f"Failed to send email: {e}")

# Example usage:
# send_email("Test Subject", "Hello, this is a test email.", "recipient@example.com", "your-email@gmail.com", "your-email-password")


bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Welcome back!', 'success')
            return redirect(url_for('main.index'))
        flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))
        
        session['email']=email
        session['password']=password
        session['username']=username
        
        body=generate_otp_email_body()
        send_email(body,email)
        return render_template('auth/verify.html')    
        
    return render_template('auth/register.html')

@bp.route("/verify", methods=['POST'])
def verify():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    otp = request.form.get('otp')
    print(otp)
    
    if not otp == session.get('otp'):
        print("session otp",session.get('otp'))
        return render_template('auth/verify.html', message="Invalid OTP")
    
    user = User(username=session['username'], email=session['email'])
    user.set_password(session['password'])
    db.session.add(user)
    db.session.commit()   
    
    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('auth.login'))
    

@bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index')) 