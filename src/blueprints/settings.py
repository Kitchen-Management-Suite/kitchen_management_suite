"""
File: settings.py
File-Path: src/blueprints/settings.py
Author: Rohan Plante
Date-Created: 12-04-2025

Description:
    Settings blueprint for handling user account settings, profile management,
    password changes, data export, and account deletion.

Inputs:
    flask request data
    database session

Outputs:
    settings pages and user data operations
"""

import json
from flask import Blueprint, Response, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from db.server import get_session
from db.schema.user import User
from db.schema.user_profile import UserProfile
from db.schema.household import Household
from db.schema.member import Member
from db.schema.role import Role

settings_bp = Blueprint('settings', __name__)


def _load_user_and_profile(db_session, user_id):
    """Helper to load user and profile, creating profile if needed"""
    user = db_session.query(User).filter(User.UserID == user_id).first()
    profile = db_session.query(UserProfile).filter(UserProfile.UserID == user_id).first()
    if not profile:
        profile = UserProfile(UserID=user_id)
        db_session.add(profile)
        db_session.commit()
    return user, profile


def _get_user_households(db_session, user_id):
    """Helper to get user's households with roles"""
    households = db_session.query(Household, Member, Role).join(
        Member, Household.HouseholdID == Member.HouseholdID
    ).join(
        Role, Member.RoleID == Role.RoleID
    ).filter(
        Member.UserID == user_id
    ).all()

    return [{
        'HouseholdID': h.HouseholdID,
        'HouseholdName': h.HouseholdName,
        'Role': r.RoleName
    } for h, _, r in households]


@settings_bp.route('/settings')
def settings():
    """Display settings page"""
    if not session.get('logged_in'):
        flash('Please log in to access settings.', 'error')
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    db_session = get_session()
    
    try:
        user, profile = _load_user_and_profile(db_session, user_id)
        user_households = _get_user_households(db_session, user_id)

        # Prepare data for template/JS
        user_data = {
            'username': user.Username,
            'email': user.Email,
            'firstName': user.FirstName or '',
            'lastName': user.LastName or '',
            'dateOfBirth': user.DateOfBirth.strftime('%Y-%m-%d') if user.DateOfBirth else ''
        }
        
        profile_data = {
            'height': profile.Height if profile else None,
            'weight': profile.Weight if profile else None,
            'calorieGoal': profile.CalorieGoal if profile else None,
            'dietaryPreferences': profile.DietaryPreferences or '' if profile else '',
            'allergies': profile.Allergies or '' if profile else ''
        }

        return render_template('settings.html',
                             user=user,
                             profile=profile or {},
                             user_data=user_data,
                             profile_data=profile_data,
                             user_households=user_households)
    except Exception as e:
        flash(f'Error loading settings: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        db_session.close()


@settings_bp.route('/settings/profile/update', methods=['POST'])
def update_profile():
    """Update user profile information"""
    if not session.get('logged_in'):
        flash('Please log in to update your profile.', 'error')
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    db_session = get_session()
    
    try:
        user = db_session.query(User).filter(User.UserID == user_id).first()
        profile = db_session.query(UserProfile).filter(UserProfile.UserID == user_id).first()
        
        if not profile:
            profile = UserProfile(UserID=user_id)
            db_session.add(profile)

        # Handle numeric fields
        numeric_fields = {
            'height': ('Height', float),
            'weight': ('Weight', float),
            'calorie_goal': ('CalorieGoal', int),
        }
        
        for form_field, (attr, parser) in numeric_fields.items():
            value = request.form.get(form_field, '').strip()
            if value:
                try:
                    setattr(profile, attr, parser(value))
                except ValueError:
                    pass

        # Handle text fields
        name_map = {
            'first_name': ('FirstName', user),
            'last_name': ('LastName', user),
            'dietary_preferences': ('DietaryPreferences', profile),
            'allergies': ('Allergies', profile),
        }
        
        for form_field, (attr, target) in name_map.items():
            value = request.form.get(form_field, '').strip()
            if value:
                setattr(target, attr, value)

        db_session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error updating profile: {str(e)}', 'error')
    finally:
        db_session.close()
        
    return redirect(url_for('settings.settings'))


@settings_bp.route('/settings/account/update', methods=['POST'])
def update_account():
    """Update account username and email"""
    if not session.get('logged_in'):
        flash('Please log in to update your account.', 'error')
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    db_session = get_session()
    
    try:
        user = db_session.query(User).filter(User.UserID == user_id).first()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()

        if not username or not email:
            flash('Username and email are required.', 'error')
            return redirect(url_for('settings.settings'))

        # Check for existing username
        if db_session.query(User).filter(User.Username == username, User.UserID != user_id).first():
            flash('Username already taken.', 'error')
            return redirect(url_for('settings.settings'))
            
        # Check for existing email
        if db_session.query(User).filter(User.Email == email, User.UserID != user_id).first():
            flash('Email already taken.', 'error')
            return redirect(url_for('settings.settings'))

        user.Username = username
        user.Email = email
        session['username'] = username
        db_session.commit()
        flash('Account updated!', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error updating account: {str(e)}', 'error')
    finally:
        db_session.close()
        
    return redirect(url_for('settings.settings'))


@settings_bp.route('/settings/password/change', methods=['POST'])
def change_password():
    """Change user password"""
    if not session.get('logged_in'):
        flash('Please log in to change your password.', 'error')
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    current = request.form.get('current_password', '')
    new = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')
    
    if not current or not new or not confirm:
        flash('All password fields are required.', 'error')
        return redirect(url_for('settings.settings'))

    if new != confirm:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('settings.settings'))

    db_session = get_session()
    try:
        user = db_session.query(User).filter(User.UserID == user_id).first()
        
        if not check_password_hash(user.Password, current):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('settings.settings'))
            
        user.Password = generate_password_hash(new)
        db_session.commit()
        flash('Password changed!', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error changing password: {str(e)}', 'error')
    finally:
        db_session.close()
        
    return redirect(url_for('settings.settings'))


@settings_bp.route('/settings/data/export', methods=['POST'])
def export_data():
    """Export user data as JSON"""
    if not session.get('logged_in'):
        flash('Please log in to export data.', 'error')
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    db_session = get_session()
    
    try:
        user = db_session.query(User).filter(User.UserID == user_id).first()
        profile = db_session.query(UserProfile).filter(UserProfile.UserID == user_id).first()
        
        payload = {
            'user': {
                'username': user.Username,
                'email': user.Email,
                'firstName': user.FirstName,
                'lastName': user.LastName
            },
            'profile': {}
        }
        
        if profile:
            payload['profile'] = {
                'height': profile.Height,
                'weight': profile.Weight,
                'calorie_goal': profile.CalorieGoal,
                'dietary_preferences': profile.DietaryPreferences,
                'allergies': profile.Allergies
            }
            
        data = json.dumps(payload, indent=2)
        return Response(
            data,
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=user_data.json'}
        )
    except Exception as e:
        flash(f'Error exporting data: {str(e)}', 'error')
        return redirect(url_for('settings.settings'))
    finally:
        db_session.close()


@settings_bp.route('/settings/household/leave', methods=['POST'])
def leave_household():
    """Leave a household"""
    if not session.get('logged_in'):
        flash('Please log in to leave a household.', 'error')
        return redirect(url_for('auth.login'))

    household_id = request.form.get('household_id')
    
    if not household_id:
        flash('Select a household.', 'error')
        return redirect(url_for('settings.settings'))

    db_session = get_session()
    try:
        member = db_session.query(Member).filter(
            Member.UserID == session['user_id'],
            Member.HouseholdID == household_id
        ).first()
        
        if not member:
            flash('Not a member of that household.', 'error')
            return redirect(url_for('settings.settings'))
            
        db_session.delete(member)
        db_session.commit()
        
        # Clear current household if leaving it
        if session.get('current_household_id') == int(household_id):
            session.pop('current_household_id', None)
            
        flash('Left household.', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error leaving household: {str(e)}', 'error')
    finally:
        db_session.close()
        
    return redirect(url_for('settings.settings'))


@settings_bp.route('/settings/account/delete', methods=['POST'])
def delete_account():
    """Delete user account"""
    if not session.get('logged_in'):
        flash('Please log in to delete your account.', 'error')
        return redirect(url_for('auth.login'))
        
    if request.form.get('confirm_delete', '') != 'DELETE':
        flash('Type DELETE to confirm.', 'error')
        return redirect(url_for('settings.settings'))

    db_session = get_session()
    try:
        user = db_session.query(User).filter(User.UserID == session['user_id']).first()
        db_session.delete(user)
        db_session.query(UserProfile).filter(UserProfile.UserID == session['user_id']).delete()
        db_session.commit()
        session.clear()
        flash('Account deleted.', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db_session.rollback()
        flash(f'Error deleting account: {str(e)}', 'error')
    finally:
        db_session.close()
        
    return redirect(url_for('settings.settings'))