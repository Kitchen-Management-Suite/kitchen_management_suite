"""
File: recipes.py
File-Path: src/blueprints/recipes.py
Author: Rohan Plante
Date-Created: 10-30-2025

Description:
    Recipes blueprint for handling recipe display and household selection

Inputs:
    flask request data
    database session

Outputs:
    recipe pages and household switching
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from db.server import get_session
from db.schema.user import User
from db.schema.household import Household
from db.schema.member import Member
from db.schema.recipe import Recipe
from db.schema.authors import Authors
from db.schema.holds import Holds
from sqlalchemy import and_, func
from datetime import datetime, date
recipes_bp = Blueprint('recipes', __name__)

@recipes_bp.route('/recipes')
def recipes():
    """Display recipes page with three carousels"""
    if not session.get('logged_in'):
        flash('Please login to view recipes', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    db_session = get_session()
    
    try:
        # Get user's households
        user_households = db_session.query(Household).join(Member).filter(
            Member.UserID == user_id
        ).all()
        
        # Get or set current household
        current_household_id = session.get('current_household_id')
        
        # If no household selected or invalid, select first one
        if not current_household_id or current_household_id not in [h.HouseholdID for h in user_households]:
            if user_households:
                current_household_id = user_households[0].HouseholdID
                session['current_household_id'] = current_household_id
            else:
                flash('You are not a member of any household', 'error')
                return render_template('recipes.html', 
                                     user_households=[],
                                     current_household_id=None,
                                     user_recipes=[],
                                     household_recipes=[],
                                     recommended_recipes=[])
        
        # Get current household object
        current_household = db_session.query(Household).get(current_household_id)
        
        # 1. User Authored Recipes (recipes this user created)
        # Get unique recipe IDs first, then fetch recipes
        user_recipe_ids = db_session.query(Authors.RecipeID).filter(
            and_(
                Authors.UserID == user_id
                )
        ).distinct().all()
        
        user_recipe_ids = [r[0] for r in user_recipe_ids]
        user_recipes = db_session.query(Recipe).filter(
            Recipe.RecipeID.in_(user_recipe_ids)
        ).all() if user_recipe_ids else []
        
        # 2. Household Recipes
        # Get unique recipe IDs first
        household_recipe_ids = db_session.query(Holds.RecipeID).filter(
            Holds.HouseholdID == current_household_id
        ).distinct().all()
        
        household_recipe_ids = [r[0] for r in household_recipe_ids]
        household_recipes = db_session.query(Recipe).filter(
            Recipe.RecipeID.in_(household_recipe_ids)
        ).all() if household_recipe_ids else []
        
        # Remove user's own recipes from household recipes to avoid duplicates
        # i think we should consider adding a tag to say if that recipe is in current household or not
        # as to not lose data
        user_recipe_id_set = set(user_recipe_ids)
        household_recipes = [r for r in household_recipes if r.RecipeID not in user_recipe_id_set]
        
        # 3. Recommended Recipes -> need to implement recommendation logic based on current items
        # as well as calorie goals.
        all_household_recipe_ids = user_recipe_id_set | set(household_recipe_ids)
        recommended_recipes = db_session.query(Recipe).filter(
            and_(
                Recipe.IsGlobal == True,
                ~Recipe.RecipeID.in_(all_household_recipe_ids) if all_household_recipe_ids else True
            )
        ).limit(20).all()
        
        return render_template('recipes.html',
                             user_households=user_households,
                             current_household_id=current_household_id,
                             current_household=current_household,
                             user_recipes=user_recipes,
                             household_recipes=household_recipes,
                             recommended_recipes=recommended_recipes)
    
    except Exception as e:
        flash(f'Error loading recipes: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        db_session.close()

@recipes_bp.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    """Display individual recipe page with pantry availability"""
    if not session.get('logged_in'):
        flash('Please login to view recipes', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    db_session = get_session()
    
    try:
        recipe = db_session.query(Recipe).get(recipe_id)
        
        if not recipe:
            flash('Recipe not found', 'error')
            return redirect(url_for('recipes.recipes'))
        
        # Get current household
        current_household_id = session.get('current_household_id')
        
        # Get pantry items for current household
        pantry_items = {}
        if current_household_id:
            from db.schema.pantry import Pantry
            from db.schema.item import Item
            from db.schema.adds import Adds
            
            # Get the household's pantry
            pantry = db_session.query(Pantry).filter(
                Pantry.HouseholdID == current_household_id
            ).first()
            
            if pantry:
                # Get all items in this pantry with quantities
                items_in_pantry = db_session.query(
                    Item.ItemName,
                    func.sum(Adds.Quantity).label('total_quantity')
                ).join(Adds).filter(
                    Adds.PantryID == pantry.PantryID
                ).group_by(Item.ItemName).all()
                
                # Create a dictionary of item names (lowercase) to quantities
                pantry_items = {
                    item.lower(): qty for item, qty in items_in_pantry
                }
        
        return render_template('recipe_detail.html', 
                             recipe=recipe,
                             pantry_items=pantry_items)
    
    except Exception as e:
        flash(f'Error loading recipe: {str(e)}', 'error')
        return redirect(url_for('recipes.recipes'))
    finally:
        db_session.close()

@recipes_bp.route('/recipes/add', methods=['POST'])
def add_recipe():
    """Add a new custom recipe"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    user_id = session.get('user_id')
    
    db_session = get_session()
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('recipeName'):
            return jsonify({'success': False, 'error': 'Recipe name is required'}), 400
        
        # Validate household selection
        selected_household_ids = data.get('householdIds', [])
        if not selected_household_ids or len(selected_household_ids) == 0:
            return jsonify({'success': False, 'error': 'Please select at least one household'}), 400
        
        # Verify user has access to selected households
        user_households = db_session.query(Member).filter(
            Member.UserID == user_id,
            Member.HouseholdID.in_(selected_household_ids)
        ).all()
        
        user_household_ids = [m.HouseholdID for m in user_households]
        
        # Check if all selected households are valid
        invalid_households = set(selected_household_ids) - set(user_household_ids)
        if invalid_households:
            return jsonify({'success': False, 'error': 'You do not have access to some selected households'}), 403
        
        # Build ingredients dictionary in Fathub format
        ingredients = {}
        for i, ing in enumerate(data.get('ingredients', [])):
            if ing.get('name'):
                key = ing['name'].lower().replace(' ', '')
                ingredients[key] = {
                    'id': ing['name'].lower().replace(' ', '-'),
                    'amount': float(ing.get('amount', 1)) if ing.get('amount') else 1,
                    'unit': ing.get('unit', 'piece')
                }
        
        # Build recipe body
        recipe_body = {
            'name': data['recipeName'],
            'author': f"{session.get('username', 'User')}",
            'created': str(date.today()),
            'serves': int(data.get('serves', 1)) if data.get('serves') else 1,
            'preptime': int(data.get('preptime', 0)) if data.get('preptime') else 0,
            'cooktime': int(data.get('cooktime', 0)) if data.get('cooktime') else 0,
            'ingredients': ingredients,
            'instructions': data.get('instructions', []),
            'cuisine': data.get('cuisine', ''),
            'course': data.get('course', 'main course')
        }
        
        # Create recipe
        new_recipe = Recipe(
            RecipeName=data['recipeName'],
            RecipeBody=recipe_body,
            Source='custom',
            IsGlobal=False
        )
        db_session.add(new_recipe)
        db_session.flush()
        
        # Add to Authors and Holds tables for each selected household
        for household_id in selected_household_ids:
            # Add to Authors table
            author_entry = Authors(
                UserID=user_id,
                HouseholdID=household_id,
                RecipeID=new_recipe.RecipeID,
                DateAdded=date.today(),
                IsCustom=True
            )
            db_session.add(author_entry)
            
            # Add to Holds table so it appears in household recipes
            holds_entry = Holds(
                HouseholdID=household_id,
                RecipeID=new_recipe.RecipeID
            )
            db_session.add(holds_entry)
        
        db_session.commit()
        
        household_names = db_session.query(Household.HouseholdName).filter(
            Household.HouseholdID.in_(selected_household_ids)
        ).all()
        household_names_list = [name[0] for name in household_names]
        
        flash(f"Recipe added to {len(selected_household_ids)} household(s): {', '.join(household_names_list)}", 'success')

        return jsonify({
            'success': True,
            'recipe_id': new_recipe.RecipeID,
            'message': f'Recipe added to {len(selected_household_ids)} household(s): {", ".join(household_names_list)}'
        })
        
    except Exception as e:
        db_session.rollback()
        print(f"Error adding recipe: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()