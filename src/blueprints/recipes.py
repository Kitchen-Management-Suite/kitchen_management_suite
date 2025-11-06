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

# Added by; Arya:

@recipes_bp.route('/recipes/create', methods=['GET', 'POST'])
def create_recipe():
    """Display and handle recipe creation form"""
    if not session.get('logged_in'):
        flash('Please login to create a recipe', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # TO DO: Handle recipe form submission here (e.g. save to DB)
        flash('Recipe created successfully!', 'success')
        return redirect(url_for('recipes.recipes'))

    # Render the recipe creation form
    return render_template('create_recipe.html')