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


# ============================================================================
# Household Settings Routes (Owner only)
# ============================================================================

def _check_household_owner():
    """Helper to verify user is Owner of current household"""
    if not session.get('logged_in'):
        return None, 'Please log in.'
    
    user_id = session.get('user_id')
    household_id = session.get('current_household_id')
    
    if not household_id:
        return None, 'No household selected.'
    
    db_session = get_session()
    try:
        member = db_session.query(Member).join(Role).filter(
            Member.UserID == user_id,
            Member.HouseholdID == household_id
        ).first()
        
        if not member or member.role.RoleName not in ['Owner', 'admin']:
            return None, 'You must be an Owner to perform this action.'
        
        return household_id, None
    finally:
        db_session.close()


@settings_bp.route('/settings/household/rename', methods=['POST'])
def rename_household():
    """Rename the current household"""
    household_id, error = _check_household_owner()
    if error:
        flash(error, 'error')
        return redirect(url_for('household_settings'))

    new_name = request.form.get('household_name', '').strip()
    
    if not new_name:
        flash('Household name is required.', 'error')
        return redirect(url_for('household_settings'))
    
    if len(new_name) > 100:
        flash('Household name must be 100 characters or less.', 'error')
        return redirect(url_for('household_settings'))

    db_session = get_session()
    try:
        # Check if name is already taken by another household
        existing = db_session.query(Household).filter(
            Household.HouseholdName == new_name,
            Household.HouseholdID != household_id
        ).first()
        
        if existing:
            flash('A household with this name already exists.', 'error')
            return redirect(url_for('household_settings'))
        
        household = db_session.query(Household).get(household_id)
        household.HouseholdName = new_name
        db_session.commit()
        
        flash('Household name updated successfully.', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error renaming household: {str(e)}', 'error')
    finally:
        db_session.close()

    return redirect(url_for('household_settings'))


@settings_bp.route('/settings/household/member/role', methods=['POST'])
def change_member_role():
    """Change a member's role in the household"""
    household_id, error = _check_household_owner()
    if error:
        flash(error, 'error')
        return redirect(url_for('household_settings'))

    member_id = request.form.get('member_id')
    new_role_id = request.form.get('role_id')
    
    if not member_id or not new_role_id:
        flash('Member and role are required.', 'error')
        return redirect(url_for('household_settings'))

    db_session = get_session()
    try:
        member = db_session.query(Member).filter(
            Member.MemberID == member_id,
            Member.HouseholdID == household_id
        ).first()
        
        if not member:
            flash('Member not found in this household.', 'error')
            return redirect(url_for('household_settings'))
        
        # Prevent removing the last Owner
        if member.role.RoleName == 'Owner':
            owner_count = db_session.query(Member).join(Role).filter(
                Member.HouseholdID == household_id,
                Role.RoleName == 'Owner'
            ).count()
            
            new_role = db_session.query(Role).get(new_role_id)
            if owner_count <= 1 and new_role.RoleName != 'Owner':
                flash('Cannot remove the last Owner. Assign another Owner first.', 'error')
                return redirect(url_for('household_settings'))
        
        member.RoleID = new_role_id
        db_session.commit()
        
        flash('Member role updated successfully.', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error changing member role: {str(e)}', 'error')
    finally:
        db_session.close()

    return redirect(url_for('household_settings'))


@settings_bp.route('/settings/household/member/remove', methods=['POST'])
def remove_member():
    """Remove a member from the household"""
    household_id, error = _check_household_owner()
    if error:
        flash(error, 'error')
        return redirect(url_for('household_settings'))

    member_id = request.form.get('member_id')
    
    if not member_id:
        flash('Member ID is required.', 'error')
        return redirect(url_for('household_settings'))

    db_session = get_session()
    try:
        member = db_session.query(Member).filter(
            Member.MemberID == member_id,
            Member.HouseholdID == household_id
        ).first()
        
        if not member:
            flash('Member not found in this household.', 'error')
            return redirect(url_for('household_settings'))
        
        # Prevent removing the last Owner
        if member.role.RoleName == 'Owner':
            owner_count = db_session.query(Member).join(Role).filter(
                Member.HouseholdID == household_id,
                Role.RoleName == 'Owner'
            ).count()
            
            if owner_count <= 1:
                flash('Cannot remove the last Owner. Assign another Owner first.', 'error')
                return redirect(url_for('household_settings'))
        
        # Prevent self-removal (use leave household instead)
        if member.UserID == session.get('user_id'):
            flash('You cannot remove yourself. Use "Leave Household" instead.', 'error')
            return redirect(url_for('household_settings'))
        
        username = member.user.Username
        db_session.delete(member)
        db_session.commit()
        
        flash(f'Member "{username}" has been removed from the household.', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error removing member: {str(e)}', 'error')
    finally:
        db_session.close()

    return redirect(url_for('household_settings'))


@settings_bp.route('/settings/household/pantry/reset', methods=['POST'])
def reset_pantry():
    """Clear all items from the household pantry"""
    household_id, error = _check_household_owner()
    if error:
        flash(error, 'error')
        return redirect(url_for('household_settings'))

    confirm = request.form.get('confirm_reset', '')
    if confirm != 'RESET':
        flash('Type RESET to confirm pantry reset.', 'error')
        return redirect(url_for('household_settings'))

    db_session = get_session()
    try:
        from db.schema.pantry import Pantry
        from db.schema.adds import Adds
        
        pantry = db_session.query(Pantry).filter(
            Pantry.HouseholdID == household_id
        ).first()
        
        if pantry:
            # Delete all items from the pantry
            deleted_count = db_session.query(Adds).filter(
                Adds.PantryID == pantry.PantryID
            ).delete()
            
            db_session.commit()
            flash(f'Pantry cleared. {deleted_count} item(s) removed.', 'success')
        else:
            flash('No pantry found for this household.', 'error')
    except Exception as e:
        db_session.rollback()
        flash(f'Error resetting pantry: {str(e)}', 'error')
    finally:
        db_session.close()

    return redirect(url_for('household_settings'))


@settings_bp.route('/settings/household/delete', methods=['POST'])
def delete_household():
    """Delete the entire household"""
    household_id, error = _check_household_owner()
    if error:
        flash(error, 'error')
        return redirect(url_for('household_settings'))

    confirm = request.form.get('confirm_delete', '')
    if confirm != 'DELETE':
        flash('Type DELETE to confirm household deletion.', 'error')
        return redirect(url_for('household_settings'))

    db_session = get_session()
    try:
        from db.schema.pantry import Pantry
        from db.schema.adds import Adds
        from db.schema.holds import Holds
        from db.schema.authors import Authors
        
        # Delete pantry items first
        pantry = db_session.query(Pantry).filter(
            Pantry.HouseholdID == household_id
        ).first()
        
        if pantry:
            db_session.query(Adds).filter(Adds.PantryID == pantry.PantryID).delete()
            db_session.delete(pantry)
        
        # Delete recipe associations
        db_session.query(Holds).filter(Holds.HouseholdID == household_id).delete()
        db_session.query(Authors).filter(Authors.HouseholdID == household_id).delete()
        
        # Delete all members
        db_session.query(Member).filter(Member.HouseholdID == household_id).delete()
        
        # Delete the household
        household = db_session.query(Household).get(household_id)
        household_name = household.HouseholdName
        db_session.delete(household)
        
        db_session.commit()
        
        # Clear current household from session
        session.pop('current_household_id', None)
        
        flash(f'Household "{household_name}" has been deleted.', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db_session.rollback()
        flash(f'Error deleting household: {str(e)}', 'error')
    finally:
        db_session.close()

    return redirect(url_for('household_settings'))


# ============================================================================
# Join Code Management Routes
# ============================================================================

@settings_bp.route('/settings/household/joincode/generate', methods=['POST'])
def generate_join_code():
    """Generate a new join code for the household"""
    household_id, error = _check_household_owner()
    if error:
        return jsonify({'success': False, 'error': error}), 403

    db_session = get_session()
    try:
        household = db_session.query(Household).get(household_id)
        if not household:
            return jsonify({'success': False, 'error': 'Household not found'}), 404
        
        new_code = household.generate_join_code()
        household.JoinCodeEnabled = True
        db_session.commit()
        
        return jsonify({
            'success': True,
            'joinCode': new_code,
            'enabled': True
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()


@settings_bp.route('/settings/household/joincode/toggle', methods=['POST'])
def toggle_join_code():
    """Enable or disable the join code"""
    household_id, error = _check_household_owner()
    if error:
        return jsonify({'success': False, 'error': error}), 403

    db_session = get_session()
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        household = db_session.query(Household).get(household_id)
        if not household:
            return jsonify({'success': False, 'error': 'Household not found'}), 404
        
        household.JoinCodeEnabled = enabled
        db_session.commit()
        
        return jsonify({
            'success': True,
            'enabled': enabled
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()


@settings_bp.route('/settings/household/joincode', methods=['GET'])
def get_join_code():
    """Get the current join code for the household"""
    household_id, error = _check_household_owner()
    if error:
        return jsonify({'success': False, 'error': error}), 403

    db_session = get_session()
    try:
        household = db_session.query(Household).get(household_id)
        if not household:
            return jsonify({'success': False, 'error': 'Household not found'}), 404
        
        return jsonify({
            'success': True,
            'joinCode': household.JoinCode,
            'enabled': household.JoinCodeEnabled or False
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()


# ============================================================================
# Join Request Management Routes
# ============================================================================

@settings_bp.route('/settings/household/requests', methods=['GET'])
def get_join_requests():
    """Get pending join requests for the household"""
    household_id, error = _check_household_owner()
    if error:
        return jsonify({'success': False, 'error': error}), 403

    db_session = get_session()
    try:
        from db.schema.join_request import JoinRequest
        from db.schema.user import User
        
        requests = db_session.query(JoinRequest, User).join(User).filter(
            JoinRequest.HouseholdID == household_id,
            JoinRequest.Status == 'pending'
        ).all()
        
        request_list = [{
            'id': req.RequestID,
            'userId': req.UserID,
            'username': user.Username,
            'firstName': user.FirstName or '',
            'lastName': user.LastName or '',
            'email': user.Email or '',
            'message': req.Message or '',
            'createdAt': req.CreatedAt.isoformat() if req.CreatedAt else None
        } for req, user in requests]
        
        return jsonify({
            'success': True,
            'requests': request_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()


@settings_bp.route('/settings/household/requests/<int:request_id>/accept', methods=['POST'])
def accept_join_request(request_id):
    """Accept a join request"""
    household_id, error = _check_household_owner()
    if error:
        return jsonify({'success': False, 'error': error}), 403

    db_session = get_session()
    try:
        from db.schema.join_request import JoinRequest
        
        join_req = db_session.query(JoinRequest).filter(
            JoinRequest.RequestID == request_id,
            JoinRequest.HouseholdID == household_id,
            JoinRequest.Status == 'pending'
        ).first()
        
        if not join_req:
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        # Get Member role
        member_role = db_session.query(Role).filter(Role.RoleName == 'Member').first()
        if not member_role:
            return jsonify({'success': False, 'error': 'Member role not found'}), 500
        
        # Check if user is already a member
        existing = db_session.query(Member).filter(
            Member.UserID == join_req.UserID,
            Member.HouseholdID == household_id
        ).first()
        
        if existing:
            join_req.Status = 'accepted'
            db_session.commit()
            return jsonify({'success': True, 'message': 'User is already a member'})
        
        # Add user as member
        new_member = Member(
            UserID=join_req.UserID,
            HouseholdID=household_id,
            RoleID=member_role.RoleID
        )
        db_session.add(new_member)
        
        join_req.Status = 'accepted'
        db_session.commit()
        
        return jsonify({'success': True, 'message': 'Request accepted'})
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()


@settings_bp.route('/settings/household/requests/<int:request_id>/deny', methods=['POST'])
def deny_join_request(request_id):
    """Deny a join request"""
    household_id, error = _check_household_owner()
    if error:
        return jsonify({'success': False, 'error': error}), 403

    db_session = get_session()
    try:
        from db.schema.join_request import JoinRequest
        
        join_req = db_session.query(JoinRequest).filter(
            JoinRequest.RequestID == request_id,
            JoinRequest.HouseholdID == household_id,
            JoinRequest.Status == 'pending'
        ).first()
        
        if not join_req:
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        join_req.Status = 'denied'
        db_session.commit()
        
        return jsonify({'success': True, 'message': 'Request denied'})
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()


# ============================================================================
# User-facing Join Routes (for users wanting to join households)
# ============================================================================

@settings_bp.route('/household/join/code', methods=['POST'])
def join_with_code():
    """Join a household using a join code"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    user_id = session.get('user_id')
    db_session = get_session()
    
    try:
        data = request.get_json()
        join_code = data.get('code', '').strip().upper()
        
        if not join_code:
            return jsonify({'success': False, 'error': 'Join code is required'}), 400
        
        # Find household by join code
        household = db_session.query(Household).filter(
            Household.JoinCode == join_code,
            Household.JoinCodeEnabled == True
        ).first()
        
        if not household:
            return jsonify({'success': False, 'error': 'Invalid or disabled join code'}), 404
        
        # Check if already a member
        existing = db_session.query(Member).filter(
            Member.UserID == user_id,
            Member.HouseholdID == household.HouseholdID
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': 'You are already a member of this household'}), 400
        
        # Get Member role
        member_role = db_session.query(Role).filter(Role.RoleName == 'Member').first()
        if not member_role:
            return jsonify({'success': False, 'error': 'Member role not found'}), 500
        
        # Add as member directly (no approval needed for code join)
        new_member = Member(
            UserID=user_id,
            HouseholdID=household.HouseholdID,
            RoleID=member_role.RoleID
        )
        db_session.add(new_member)
        db_session.commit()
        
        # Set as current household if none selected
        if not session.get('current_household_id'):
            session['current_household_id'] = household.HouseholdID
        
        return jsonify({
            'success': True,
            'message': f'Successfully joined "{household.HouseholdName}"',
            'householdId': household.HouseholdID,
            'householdName': household.HouseholdName
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()


@settings_bp.route('/household/join/request', methods=['POST'])
def request_to_join():
    """Request to join a household (requires approval)"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    user_id = session.get('user_id')
    db_session = get_session()
    
    try:
        from db.schema.join_request import JoinRequest
        from sqlalchemy import func
        
        data = request.get_json()
        household_name = data.get('householdName', '').strip()
        message = data.get('message', '').strip()
        
        if not household_name:
            return jsonify({'success': False, 'error': 'Household name is required'}), 400
        
        # Find household by name
        household = db_session.query(Household).filter(
            func.lower(Household.HouseholdName) == func.lower(household_name)
        ).first()
        
        if not household:
            return jsonify({'success': False, 'error': 'Household not found'}), 404
        
        # Check if already a member
        existing_member = db_session.query(Member).filter(
            Member.UserID == user_id,
            Member.HouseholdID == household.HouseholdID
        ).first()
        
        if existing_member:
            return jsonify({'success': False, 'error': 'You are already a member of this household'}), 400
        
        # Check if already has a pending request
        existing_request = db_session.query(JoinRequest).filter(
            JoinRequest.UserID == user_id,
            JoinRequest.HouseholdID == household.HouseholdID,
            JoinRequest.Status == 'pending'
        ).first()
        
        if existing_request:
            return jsonify({'success': False, 'error': 'You already have a pending request for this household'}), 400
        
        # Create join request
        join_request = JoinRequest(
            UserID=user_id,
            HouseholdID=household.HouseholdID,
            Message=message if message else None
        )
        db_session.add(join_request)
        db_session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Request sent to join "{household.HouseholdName}". Waiting for approval.'
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()


@settings_bp.route('/household/requests/pending', methods=['GET'])
def get_user_pending_requests():
    """Get the current user's pending join requests"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    user_id = session.get('user_id')
    db_session = get_session()
    
    try:
        from db.schema.join_request import JoinRequest
        
        requests = db_session.query(JoinRequest, Household).join(Household).filter(
            JoinRequest.UserID == user_id,
            JoinRequest.Status == 'pending'
        ).all()
        
        request_list = [{
            'id': req.RequestID,
            'householdId': req.HouseholdID,
            'householdName': household.HouseholdName,
            'status': req.Status,
            'createdAt': req.CreatedAt.isoformat() if req.CreatedAt else None
        } for req, household in requests]
        
        return jsonify({
            'success': True,
            'requests': request_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()


@settings_bp.route('/household/requests/<int:request_id>/cancel', methods=['POST'])
def cancel_join_request(request_id):
    """Cancel a pending join request"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    user_id = session.get('user_id')
    db_session = get_session()
    
    try:
        from db.schema.join_request import JoinRequest
        
        join_req = db_session.query(JoinRequest).filter(
            JoinRequest.RequestID == request_id,
            JoinRequest.UserID == user_id,
            JoinRequest.Status == 'pending'
        ).first()
        
        if not join_req:
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        db_session.delete(join_req)
        db_session.commit()
        
        return jsonify({'success': True, 'message': 'Request cancelled'})
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()