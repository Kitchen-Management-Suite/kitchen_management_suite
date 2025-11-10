"""
File: pantry.py
File-Path: src/blueprints/pantry.py
Author: Thomas Bruce
Date-Created: 11-05-2025

Description:
    pantry blueprint for handling pantry display and item management

Inputs:
    flask request data
    database session

Outputs:
    pantry pages and item operations
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db.server import get_session
from db.schema.household import Household
from db.schema.member import Member
from db.schema.pantry import Pantry
from db.schema.item import Item
from db.schema.adds import Adds
from sqlalchemy import func

pantry_bp = Blueprint('pantry', __name__)

@pantry_bp.route('/pantry')
def pantry():
    """Display pantry page with items for current household"""
    if not session.get('logged_in'):
        flash('Please login to view pantry', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    db_session = get_session()
    
    try:
        user_households = db_session.query(Household).join(Member).filter(
            Member.UserID == user_id
        ).all()
        
        if not user_households:
            flash('You are not a member of any household', 'error')
            return render_template('pantry.html',
                                 current_household=None,
                                 pantry_items=[])
        
        current_household_id = session.get('current_household_id')
        
        if not current_household_id or current_household_id not in [h.HouseholdID for h in user_households]:
            current_household_id = user_households[0].HouseholdID
            session['current_household_id'] = current_household_id
        
        current_household = db_session.query(Household).get(current_household_id)
        
        pantry = db_session.query(Pantry).filter(
            Pantry.HouseholdID == current_household_id
        ).first()
        
        pantry_items = []
        if pantry:
            items_with_quantities = db_session.query(
                Item,
                func.sum(Adds.Quantity).label('total_quantity')
            ).join(Adds).filter(
                Adds.PantryID == pantry.PantryID
            ).group_by(Item.ItemID).all()
            
            pantry_items = [
                {
                    'ItemName': item.ItemName,
                    'Quantity': quantity
                }
                for item, quantity in items_with_quantities
            ]
        
        return render_template('pantry.html',
                             current_household=current_household,
                             pantry_items=pantry_items)
    
    except Exception as e:
        flash(f'Error loading pantry: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        db_session.close()

