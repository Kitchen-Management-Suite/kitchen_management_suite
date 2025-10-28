"""
File: auth.py
File-Path: src/auth.py
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

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        dob = request.form.get('dob')
        
        # validate required fields
        if not all([username, email, password, dob]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        db_session = get_session()
        try:
            # check if user already exists
            existing_user = db_session.query(User).filter(
                (User.Username == username) | (User.Email == email)
            ).first()
            
            if existing_user:
                flash('Username or email already exists', 'error')
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
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db_session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return render_template('register.html')
        finally:
            db_session.close()
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([email, password]):
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        db_session = get_session()
        try:
            user = db_session.query(User).filter(User.Email == email).first()
            
            if user and check_password_hash(user.Password, password):
                # set session data
                session['user_id'] = user.UserID
                session['username'] = user.Username
                session['logged_in'] = True
                
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password', 'error')
                return render_template('login.html')
                
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
            return render_template('login.html')
        finally:
            db_session.close()
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

