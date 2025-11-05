"""
File: validation_helper.py
File-Path: src/helpers/validation_helper.py
Author: Thomas Bruce
Date-Created: 11-04-2025

Description:
    server-side validation helper

Inputs:
    user input data

Outputs:
    validation errors
"""

import re
from datetime import datetime, date
from typing import Dict


def validate_registration_data(username: str, email: str, password: str, dob: str) -> Dict[str, str]:
    """validates registration data and returns errors dict"""
    errors = {}
    
    # username
    if not username or not username.strip():
        errors['username'] = "Username is required"
    elif len(username.strip()) < 3:
        errors['username'] = "Username must be at least 3 characters"
    elif len(username.strip()) > 50:
        errors['username'] = "Username must be less than 50 characters"
    elif not re.match(r'^[a-zA-Z0-9_-]+$', username.strip()):
        errors['username'] = "Username can only contain letters, numbers, hyphens, and underscores"
    
    # email
    if not email:
        errors['email'] = "Email is required"
    elif len(email.strip()) > 254:
        errors['email'] = "Email address is too long"
    elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email.strip()):
        errors['email'] = "Please enter a valid email address"
    
    # password
    if not password:
        errors['password'] = "Password is required"
    elif len(password) < 6:
        errors['password'] = "Password must be at least 6 characters"
    elif len(password) > 128:
        errors['password'] = "Password must be less than 128 characters"
    
    # date of birth
    if not dob:
        errors['dob'] = "Date of birth is required"
    else:
        try:
            birth_date = datetime.strptime(dob, '%Y-%m-%d').date()
            today = date.today()
            
            if birth_date > today:
                errors['dob'] = "Date of birth cannot be in the future"
            else:
                age = today.year - birth_date.year
                if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                    age -= 1
                
                if age < 13:
                    errors['dob'] = "You must be at least 13 years old to register"
                elif age > 120:
                    errors['dob'] = "Please enter a valid date of birth"
        except ValueError:
            errors['dob'] = "Invalid date format"
    
    return errors


def validate_login_data(email: str, password: str) -> Dict[str, str]:
    """validates login data and returns errors dict"""
    errors = {}
    
    if not email:
        errors['email'] = "Email is required"
    elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email.strip()):
        errors['email'] = "Please enter a valid email address"
    
    if not password:
        errors['password'] = "Password is required"
    
    return errors

