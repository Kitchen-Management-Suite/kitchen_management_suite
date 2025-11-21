"""
File: navbar_helper.py
File-Path: src/helpers/navbar_helper.py
Author: Rohan Plante
Date-Created: 11/01/2025

Description:
    Helper functions to inject navbar data into templates
    Provides household management for logged in users
"""

from flask import session, request
from db.server import get_session
from db.schema.member import Member
from db.schema.household import Household
from db.schema.user import User
from db.schema.role import Role

def get_current_household_id():
    """
    Get the currently selected household ID from session
    
    Returns:
        int or None: Current household ID
    """
    return session.get('current_household_id')


def set_current_household_id(household_id):
    """
    Set the currently selected household ID in session
    
    Args:
        household_id (int): Household ID to set as current
    """
    session['current_household_id'] = household_id


def get_user_households():
    """
    Get all households the current user belongs to

    Returns:
        list: List of Household objects, empty list if not logged in
    """
    if not session.get('logged_in'):
        return []

    user_id = session.get('user_id')
    if not user_id:
        return []

    db_session = get_session()
    try:
        memberships = db_session.query(Member).filter_by(UserID=user_id).all()
        household_ids = [m.HouseholdID for m in memberships]

        if household_ids:
            households = db_session.query(Household).filter(
                Household.HouseholdID.in_(household_ids)
            ).all()
            return households
        return []
    except Exception as e:
        print(f"Error fetching user households: {e}")
        return []
    finally:
        db_session.close()


def get_user_households_with_roles():
    """
    Get all households the current user belongs to, with role information

    Returns:
        list: List of dicts with household and role info, empty list if not logged in
    """
    if not session.get('logged_in'):
        return []

    user_id = session.get('user_id')
    if not user_id:
        return []

    db_session = get_session()
    try:
        # Join Member and Household tables to get household data with role
        memberships = db_session.query(Member, Household).join(
            Household, Member.HouseholdID == Household.HouseholdID
        ).filter(Member.UserID == user_id).all()

        households_with_roles = []
        for member, household in memberships:
            households_with_roles.append({
                'HouseholdID': household.HouseholdID,
                'HouseholdName': household.HouseholdName,
                'Role': member.role.RoleName if member.role else 'Unknown'
            })

        return households_with_roles
    except Exception as e:
        print(f"Error fetching user households with roles: {e}")
        return []
    finally:
        db_session.close()


def get_user_full_name():
    """
    Get the user's full name from the database
    
    Returns:
        str: User's full name or username if name not available
    """
    if not session.get('logged_in'):
        return 'User'
    
    user_id = session.get('user_id')
    if not user_id:
        return session.get('username', 'User')
    
    db_session = get_session()
    try:
        user = db_session.query(User).filter_by(UserID=user_id).first()
        if user:
            # If FirstName and LastName exist, use them
            if user.FirstName and user.LastName:
                return f"{user.FirstName} {user.LastName}"
            # If only FirstName exists
            elif user.FirstName:
                return user.FirstName
            else:
                return user.Username
        return session.get('username', 'User')
    except Exception as e:
        print(f"Error fetching user name: {e}")
        return session.get('username', 'User')
    finally:
        db_session.close()


def get_user_role_in_household(user_id, household_id):
    """
    Get the user's role in a specific household

    Args:
        user_id (int): User ID
        household_id (int): Household ID

    Returns:
        str or None: Role name, or None if not found
    """
    if not user_id or not household_id:
        return None

    db_session = get_session()
    try:
        membership = db_session.query(Member).filter_by(
            UserID=user_id,
            HouseholdID=household_id
        ).first()

        if membership and membership.role:
            return membership.role.RoleName
        return None
    except Exception as e:
        print(f"Error fetching user role: {e}")
        return None
    finally:
        db_session.close()


def get_current_user_role():
    """
    Get the current user's role in the currently selected household

    Returns:
        str or None: Role name, or None if not found
    """
    user_id = session.get('user_id')
    household_id = get_current_household_id()

    return get_user_role_in_household(user_id, household_id)


def get_navbar_data(show_household_selector=True):
    """
    Get navbar data for the current user including household memberships
    
    Args:
        show_household_selector (bool): Whether to show household selector on this page
    
    Returns:
        dict: Navbar configuration data for JavaScript
    """
    current_endpoint = request.endpoint or 'index'
    
    if not session.get('logged_in'):
        return {
            'isLoggedIn': False,
            'households': [],
            'currentHouseholdId': None,
            'showHouseholdSelector': False,
            'currentEndpoint': current_endpoint,
            'userName': 'User',
            'username': 'username'
        }
    
    # Get user's households
    households = get_user_households()
    current_household_id = get_current_household_id()
    
    # If no household is selected but user has households, select the first one
    if current_household_id is None and households:
        current_household_id = households[0].HouseholdID
        set_current_household_id(current_household_id)
    
    # Convert households to dict format for JSON
    household_list = [
        {
            'id': h.HouseholdID,
            'name': h.HouseholdName
        }
        for h in households
    ]
    
    # Get user info
    user_full_name = get_user_full_name()
    username = session.get('username', 'username')

    # Get current user role
    current_user_role = get_current_user_role()
    is_admin = current_user_role == 'admin'

    return {
        'isLoggedIn': True,
        'households': household_list,
        'currentHouseholdId': current_household_id,
        'showHouseholdSelector': show_household_selector,
        'currentEndpoint': current_endpoint,
        'userName': user_full_name,
        'username': username,
        'userRole': current_user_role,
        'isAdmin': is_admin
    }


def inject_navbar_context():
    """
    Flask context processor to inject navbar data
    
    Returns:
        dict: Context variables for templates
    """
    current_endpoint = request.endpoint or ''
    show_selector = True
    
    navbar_data = get_navbar_data(show_household_selector=show_selector)

    return {
        'navbar_data': navbar_data,
        'user_households': get_user_households(),
        'current_household_id': get_current_household_id(),
        'show_household_selector': show_selector,
        'user_role': navbar_data.get('userRole'),
        'is_admin': navbar_data.get('isAdmin', False)
    }