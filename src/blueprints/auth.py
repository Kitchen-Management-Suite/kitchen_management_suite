"""
File: auth.py
File-Path: src/blueprints/auth.py
Author: Thomas Bruce
Date-Created: 10-28-2025

Description:
    authentication handler for user registration and login

Inputs:
    flask request data
    database session

Outputs:
    state of authentication
    session
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from db.server import get_session
from db.schema.user import User
from helpers.validation_helper import validate_registration_data, validate_login_data
from helpers.logging_helper import log_auth

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """handle user registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        dob = request.form.get('dob', '')
        
        validation_errors = validate_registration_data(username, email, password, dob)
        
        if validation_errors:
            for field, error in validation_errors.items():
                flash(f'{field.capitalize()}: {error}', 'error')
            
            log_auth(f"Registration failed - {username} ({email}) - validation errors", 'warning')
            return render_template('register.html')
        
        db_session = get_session()
        try:
            # check if user already exists
            existing_user = db_session.query(User).filter(
                (User.Username == username) | (User.Email == email)
            ).first()
            
            if existing_user:
                flash('Username or email already exists', 'error')
                log_auth(f"Registration failed - {username} ({email}) - already exists", 'warning')
                return render_template('register.html')
            
            # hash password and create new user
            hashed_password = generate_password_hash(password)
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            
            new_user = User(
                Username=username,
                Email=email,
                Password=hashed_password,
                DateOfBirth=dob_date
            )
            
            db_session.add(new_user)
            db_session.commit()
            
            log_auth(f"Registration successful - {username} ({email})")
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db_session.rollback()
            log_auth(f"Registration error - {username} ({email}) - {str(e)}", 'error')
            flash(f'Registration failed: An error occurred. Please try again.', 'error')
            return render_template('register.html')
        finally:
            db_session.close()
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """handle user login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        validation_errors = validate_login_data(email, password)
        
        if validation_errors:
            for field, error in validation_errors.items():
                flash(error, 'error')
            
            log_auth(f"Login failed - {email} - validation errors", 'warning')
            return render_template('login.html')
        
        db_session = get_session()
        try:
            user = db_session.query(User).filter(User.Email == email).first()
            
            if user and check_password_hash(user.Password, password):
                session['user_id'] = user.UserID
                session['username'] = user.Username
                session['logged_in'] = True
                
                log_auth(f"Login successful - {email}")
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                log_auth(f"Login failed - {email} - invalid credentials", 'warning')
                flash('Invalid email or password', 'error')
                return render_template('login.html')
                
        except Exception as e:
            log_auth(f"Login error - {email} - {str(e)}", 'error')
            flash(f'Login failed: An error occurred. Please try again.', 'error')
            return render_template('login.html')
        finally:
            db_session.close()
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """handle user logout"""
    username = session.get('username', 'unknown')
    log_auth(f"Logout - {username}")
    
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

