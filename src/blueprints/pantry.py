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

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from db.server import get_session
from db.schema.household import Household
from db.schema.member import Member
from db.schema.pantry import Pantry
from db.schema.item import Item
from db.schema.adds import Adds
from helpers.api_helper import searchByStr
from sqlalchemy import func
from datetime import date

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
            # Get items with their quantities and units
            items_with_data = db_session.query(
                Item,
                Adds.Quantity,
                Adds.Unit
            ).join(Adds).filter(
                Adds.PantryID == pantry.PantryID
            ).all()

            # Group by item and aggregate quantities by unit
            from collections import defaultdict
            item_dict = defaultdict(lambda: defaultdict(float))

            for item, quantity, unit in items_with_data:
                item_dict[item.ItemName][unit or 'pieces'] += quantity

            # Convert to list format
            pantry_items = [
                {
                    'ItemName': item_name,
                    'Quantities': [{'amount': qty, 'unit': unit} for unit, qty in units.items()]
                }
                for item_name, units in item_dict.items()
            ]

        return render_template('pantry.html',
                             current_household=current_household,
                             pantry_items=pantry_items)

    except Exception as e:
        flash(f'Error loading pantry: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        db_session.close()


@pantry_bp.route('/pantry/search_items', methods=['POST'])
def search_items():
    """Search for items using OpenFoodFacts API"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        page = data.get('page', 1)
        page_size = data.get('page_size', 10)

        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'}), 400

        # Use the same API helper as calorie tracking
        response = searchByStr(query, page=page, page_size=page_size)

        if response == -1:
            return jsonify({'success': False, 'error': 'API call failed'}), 500

        products = response.get('products', [])

        return jsonify({
            'success': True,
            'products': products,
            'page': page,
            'page_size': page_size,
            'total': response.get('count', len(products))
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@pantry_bp.route('/pantry/add_item', methods=['POST'])
def add_item():
    """Add an item to the current household's pantry"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    user_id = session.get('user_id')
    current_household_id = session.get('current_household_id')

    if not current_household_id:
        return jsonify({'success': False, 'error': 'No household selected'}), 400

    db_session = get_session()

    try:
        data = request.get_json()
        item_name = data.get('itemName', '').strip()
        quantity = data.get('quantity', 1)
        unit = data.get('unit', 'pieces')
        source = data.get('source', 'custom')
        api_data = data.get('apiData')

        if not item_name:
            return jsonify({'success': False, 'error': 'Item name is required'}), 400

        # Get or create the pantry for this household
        pantry = db_session.query(Pantry).filter(
            Pantry.HouseholdID == current_household_id
        ).first()

        if not pantry:
            # Create pantry if it doesn't exist
            pantry = Pantry(HouseholdID=current_household_id)
            db_session.add(pantry)
            db_session.flush()

        # Check if item already exists (to avoid duplicates)
        existing_item = db_session.query(Item).filter(
            Item.ItemName == item_name,
            Item.Source == source
        ).first()

        if existing_item:
            item = existing_item
        else:
            # Create new item
            item = Item(
                ItemName=item_name,
                ItemBody=api_data,
                Source=source,
                IsGlobal=False
            )
            db_session.add(item)
            db_session.flush()

        # Create the Adds record (linking user, item, and pantry)
        adds_record = Adds(
            UserID=user_id,
            PantryID=pantry.PantryID,
            ItemID=item.ItemID,
            Quantity=float(quantity),
            Unit=unit,  # Store the unit
            ItemInDate=date.today()
        )
        db_session.add(adds_record)
        db_session.commit()

        return jsonify({
            'success': True,
            'item': {
                'ItemName': item.ItemName,
                'Quantity': quantity,
                'Unit': unit
            }
        })

    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

