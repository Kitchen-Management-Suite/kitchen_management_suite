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
    
    return {
        'isLoggedIn': True,
        'households': household_list,
        'currentHouseholdId': current_household_id,
        'showHouseholdSelector': show_household_selector,
        'currentEndpoint': current_endpoint,
        'userName': user_full_name,
        'username': username
    }


def inject_navbar_context():
    """
    Flask context processor to inject navbar data
    
    Returns:
        dict: Context variables for templates
    """
    current_endpoint = request.endpoint or ''
    show_selector = True
    
    return {
        'navbar_data': get_navbar_data(show_household_selector=show_selector),
        'user_households': get_user_households(),
        'current_household_id': get_current_household_id(),
        'show_household_selector': show_selector
    }