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
from db.schema.role import Role
from db.schema.recipe import Recipe
from db.schema.authors import Authors
from db.schema.holds import Holds
from helpers.api_helper import calculate_recipe_nutrition
from helpers.unit_converter import UnitConverter
from sqlalchemy import and_, func
from datetime import datetime, date
recipes_bp = Blueprint('recipes', __name__)


def _score_and_rank_recipes(recipes, pantry_items, pantry_items_with_units=None):
    """
    Score recipes based on how many ingredients are available in the pantry.
    Returns recipes sorted by match score (highest first), limited to top 20.

    Args:
        recipes: List of Recipe objects to score
        pantry_items: Dict of {item_name_lowercase: total_quantity} from pantry (for backwards compatibility)
        pantry_items_with_units: Dict of {item_name_lowercase: [(quantity, unit), ...]} for unit-aware matching

    Returns:
        List of tuples: (Recipe object, match_data dict)
    """
    scored_recipes = []

    for recipe in recipes:
        if not recipe.RecipeBody or not isinstance(recipe.RecipeBody, dict):
            continue

        ingredients = recipe.RecipeBody.get('ingredients', {})
        if not ingredients:
            continue

        total_ingredients = len(ingredients)
        matched_ingredients = 0

        # Check each recipe ingredient against pantry
        for ing_key, ing_data in ingredients.items():
            if not isinstance(ing_data, dict):
                continue

            # Try to match ingredient name (check multiple variations)
            ing_name = ing_data.get('id', ing_key).lower()
            required_amount = float(ing_data.get('amount', 0))
            required_unit = ing_data.get('unit', 'pieces')

            # Simple matching: check if ingredient name is in pantry items
            # Also check partial matches (e.g., "chicken" matches "chicken breast")
            matched = False
            for pantry_item in pantry_items.keys():
                if (ing_name in pantry_item or
                    pantry_item in ing_name or
                    ing_name.replace('-', ' ') in pantry_item or
                    pantry_item in ing_name.replace('-', ' ')):

                    # If we have unit data, do unit-aware comparison
                    if pantry_items_with_units and pantry_item in pantry_items_with_units:
                        pantry_qty_units = pantry_items_with_units[pantry_item]

                        # Sum available quantities in base units
                        total_available = 0
                        for avail_qty, avail_unit in pantry_qty_units:
                            try:
                                if UnitConverter.can_convert_between(avail_unit, required_unit):
                                    avail_base, _ = UnitConverter.convert_to_base_unit(
                                        avail_qty, avail_unit, pantry_item
                                    )
                                    total_available += avail_base
                                else:
                                    # Different unit types, just count as having some
                                    total_available += avail_qty
                            except:
                                total_available += avail_qty

                        # Check if we have enough
                        try:
                            required_base, _ = UnitConverter.convert_to_base_unit(
                                required_amount, required_unit, ing_name
                            )
                            if total_available >= required_base:
                                matched = True
                        except:
                            # If conversion fails, just check if we have any
                            if total_available > 0:
                                matched = True
                    else:
                        # No unit data, just count as matched if we have the item
                        matched = True

                    if matched:
                        matched_ingredients += 1
                        break

        # Calculate match percentage
        match_score = (matched_ingredients / total_ingredients * 100) if total_ingredients > 0 else 0

        # Add recipe with its score
        match_data = {
            'score': round(match_score, 1),
            'matched': matched_ingredients,
            'total': total_ingredients
        }

        scored_recipes.append({
            'recipe': recipe,
            'match_data': match_data
        })

    # Sort by score (highest first), then by total ingredients (fewer ingredients = simpler recipe)
    scored_recipes.sort(key=lambda x: (x['match_data']['score'], -x['match_data']['total']), reverse=True)

    # Return top 20 recipes as tuples of (recipe, match_data)
    return [(item['recipe'], item['match_data']) for item in scored_recipes[:20]]


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

        # Check if user is admin in current household
        user_is_admin = db_session.query(Member).join(Role).filter(
            Member.UserID == user_id,
            Member.HouseholdID == current_household_id,
            Role.RoleName == 'admin'
        ).first() is not None

        # Check if user can add recipes (admin or member role)
        user_can_add_recipes = db_session.query(Member).join(Role).filter(
            Member.UserID == user_id,
            Member.HouseholdID == current_household_id,
            Role.RoleName.in_(['admin', 'member'])
        ).first() is not None

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

        # Keep user's own recipes in household recipes for easier management
        user_recipe_id_set = set(user_recipe_ids)

        # 3. Recommended Recipes based on pantry availability
        from db.schema.pantry import Pantry
        from db.schema.item import Item
        from db.schema.adds import Adds

        # Get pantry items for current household with units
        pantry_items = {}
        pantry_items_with_units = {}  # {item_name: [(quantity, unit), ...]}
        if current_household_id:
            pantry = db_session.query(Pantry).filter(
                Pantry.HouseholdID == current_household_id
            ).first()

            if pantry:
                # Get items with their quantities and units
                items_in_pantry = db_session.query(
                    Item.ItemName,
                    Adds.Quantity,
                    Adds.Unit
                ).join(Adds).filter(
                    Adds.PantryID == pantry.PantryID
                ).all()

                # Group by item name and collect all quantity-unit pairs
                from collections import defaultdict
                items_by_name = defaultdict(list)
                for item_name, qty, unit in items_in_pantry:
                    items_by_name[item_name.lower()].append((qty, unit or 'pieces'))

                pantry_items_with_units = dict(items_by_name)

                # For simple matching, also keep sum of quantities (backwards compatibility)
                pantry_items = {
                    item.lower(): sum(q for q, u in qty_units)
                    for item, qty_units in pantry_items_with_units.items()
                }

        all_household_recipe_ids = user_recipe_id_set | set(household_recipe_ids)
        candidate_recipes = db_session.query(Recipe).filter(
            and_(
                Recipe.IsGlobal == True,
                ~Recipe.RecipeID.in_(all_household_recipe_ids) if all_household_recipe_ids else True
            )
        ).all()

        # Score recipes based on pantry match (with unit-aware comparison)
        recommended_with_scores = _score_and_rank_recipes(
            candidate_recipes, pantry_items, pantry_items_with_units
        )

        # Separate recipes and match data for template
        recommended_recipes = []
        recipe_match_scores = {}
        for recipe, match_data in recommended_with_scores:
            recommended_recipes.append(recipe)
            recipe_match_scores[recipe.RecipeID] = match_data

        # Get set of recipe IDs already in current household
        household_recipe_ids_set = set(household_recipe_ids) | user_recipe_id_set

        return render_template('recipes.html',
                             user_households=user_households,
                             current_household_id=current_household_id,
                             current_household=current_household,
                             user_recipes=user_recipes,
                             household_recipes=household_recipes,
                             recommended_recipes=recommended_recipes,
                             recipe_match_scores=recipe_match_scores,
                             user_is_admin=user_is_admin,
                             user_can_add_recipes=user_can_add_recipes,
                             household_recipe_ids=household_recipe_ids_set)
    
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
        
        # Get pantry items for current household with units
        pantry_items = {}
        pantry_items_with_units = {}
        if current_household_id:
            from db.schema.pantry import Pantry
            from db.schema.item import Item
            from db.schema.adds import Adds

            # Get the household's pantry
            pantry = db_session.query(Pantry).filter(
                Pantry.HouseholdID == current_household_id
            ).first()

            if pantry:
                # Get all items in this pantry with quantities and units
                items_in_pantry = db_session.query(
                    Item.ItemName,
                    Adds.Quantity,
                    Adds.Unit
                ).join(Adds).filter(
                    Adds.PantryID == pantry.PantryID
                ).all()

                # Group by item name and collect all quantity-unit pairs
                from collections import defaultdict
                items_by_name = defaultdict(list)
                for item_name, qty, unit in items_in_pantry:
                    items_by_name[item_name.lower()].append((qty, unit or 'pieces'))

                pantry_items_with_units = dict(items_by_name)

                # For display, also keep simple dict (backwards compatibility)
                pantry_items = {
                    item.lower(): sum(q for q, _ in qty_units)
                    for item, qty_units in pantry_items_with_units.items()
                }

        # Build ingredient availability data with unit-aware quantity comparison
        ingredient_availability = {}
        if recipe.RecipeBody and recipe.RecipeBody.get('ingredients'):
            for ing_key, ing_data in recipe.RecipeBody['ingredients'].items():
                if not isinstance(ing_data, dict):
                    continue

                ing_name = ing_data.get('id', ing_key).replace('-', ' ').lower()
                required_amount = float(ing_data.get('amount', 0))
                required_unit = ing_data.get('unit', 'pieces')

                # Check pantry for this ingredient
                matched_pantry_items = []
                matched_pantry_name = None

                for pantry_item, qty_units in pantry_items_with_units.items():
                    if ing_name in pantry_item or pantry_item in ing_name:
                        matched_pantry_items = qty_units
                        matched_pantry_name = pantry_item
                        break

                # Determine availability status using unit-aware comparison
                status = 'none'
                available_display = 0
                required_display = required_amount

                if matched_pantry_items:
                    # Sum up all available quantities in the same unit as required
                    total_available_in_base = 0
                    has_convertible = False

                    for available_qty, available_unit in matched_pantry_items:
                        # Try to convert both to a common base unit for comparison
                        try:
                            can_convert = UnitConverter.can_convert_between(
                                available_unit, required_unit
                            )

                            if can_convert:
                                has_convertible = True
                                # Convert available quantity to required unit's base
                                avail_base, avail_base_unit = UnitConverter.convert_to_base_unit(
                                    available_qty, available_unit, matched_pantry_name
                                )
                                total_available_in_base += avail_base
                        except:
                            # If conversion fails, just add the quantity directly
                            total_available_in_base += available_qty

                    if has_convertible or matched_pantry_items:
                        # Convert required amount to base unit
                        try:
                            required_base, required_base_unit = UnitConverter.convert_to_base_unit(
                                required_amount, required_unit, ing_name
                            )
                        except:
                            required_base = required_amount
                            required_base_unit = required_unit

                        # Compare in base units
                        if total_available_in_base >= required_base:
                            status = 'full'
                            available_display = f"{total_available_in_base:.1f}{required_base_unit}"
                        elif total_available_in_base > 0:
                            status = 'partial'
                            available_display = f"{total_available_in_base:.1f}{required_base_unit}"

                        required_display = f"{required_base:.1f}{required_base_unit}"
                    else:
                        # Fallback: just show we have some
                        status = 'partial'
                        total_qty = sum(q for q, _ in matched_pantry_items)
                        available_display = f"{total_qty:.1f}"

                ingredient_availability[ing_name] = {
                    'status': status,
                    'available': available_display,
                    'required': required_display
                }

        return render_template('recipe_detail.html',
                             recipe=recipe,
                             pantry_items=pantry_items,
                             ingredient_availability=ingredient_availability)
    
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
        
        # Calculate nutrition automatically
        servings = int(data.get('serves', 1)) if data.get('serves') else 1
        nutriments_per_serving = None

        if ingredients:
            try:
                nutriments_per_serving = calculate_recipe_nutrition(ingredients, servings)
            except Exception as e:
                print(f"Failed to calculate nutrition: {e}")
                # Continue without nutrition data

        # Build recipe body
        recipe_body = {
            'name': data['recipeName'],
            'author': f"{session.get('username', 'User')}",
            'created': str(date.today()),
            'serves': servings,
            'preptime': int(data.get('preptime', 0)) if data.get('preptime') else 0,
            'cooktime': int(data.get('cooktime', 0)) if data.get('cooktime') else 0,
            'ingredients': ingredients,
            'instructions': data.get('instructions', []),
            'cuisine': data.get('cuisine', ''),
            'course': data.get('course', 'main course')
        }

        # Add nutrition data if available
        if nutriments_per_serving:
            recipe_body['nutriments_per_serving'] = nutriments_per_serving

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


@recipes_bp.route('/recipes/match_info/<int:recipe_id>', methods=['GET'])
def get_recipe_match_info(recipe_id):
    """Get detailed ingredient match information for a recipe"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    current_household_id = session.get('current_household_id')
    if not current_household_id:
        return jsonify({'success': False, 'error': 'No household selected'}), 400

    db_session = get_session()

    try:
        recipe = db_session.query(Recipe).get(recipe_id)
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found'}), 404

        # Get pantry items
        from db.schema.pantry import Pantry
        from db.schema.item import Item
        from db.schema.adds import Adds

        pantry_items = {}
        pantry = db_session.query(Pantry).filter(
            Pantry.HouseholdID == current_household_id
        ).first()

        if pantry:
            items_in_pantry = db_session.query(
                Item.ItemName,
                func.sum(Adds.Quantity).label('total_quantity')
            ).join(Adds).filter(
                Adds.PantryID == pantry.PantryID
            ).group_by(Item.ItemName).all()

            pantry_items = {
                item.lower(): qty for item, qty in items_in_pantry
            }

        # Analyze ingredients
        ingredients = recipe.RecipeBody.get('ingredients', {}) if recipe.RecipeBody else {}

        ingredient_details = []
        matched_count = 0

        for ing_key, ing_data in ingredients.items():
            if not isinstance(ing_data, dict):
                continue

            ing_name = ing_data.get('id', ing_key).replace('-', ' ')
            ing_amount = ing_data.get('amount', 0)
            ing_unit = ing_data.get('unit', '')

            # Check if available in pantry
            is_available = False
            for pantry_item in pantry_items.keys():
                if (ing_name.lower() in pantry_item or
                    pantry_item in ing_name.lower()):
                    is_available = True
                    matched_count += 1
                    break

            ingredient_details.append({
                'name': ing_name.title(),
                'amount': ing_amount,
                'unit': ing_unit,
                'available': is_available
            })

        total_ingredients = len(ingredient_details)
        match_percentage = (matched_count / total_ingredients * 100) if total_ingredients > 0 else 0

        return jsonify({
            'success': True,
            'recipe_id': recipe_id,
            'recipe_name': recipe.RecipeName,
            'matched': matched_count,
            'total': total_ingredients,
            'match_percentage': round(match_percentage, 1),
            'ingredients': ingredient_details
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()


@recipes_bp.route('/recipes/calculate_nutrition/<int:recipe_id>', methods=['POST'])
def calculate_nutrition_for_recipe(recipe_id):
    """Calculate or recalculate nutrition for an existing recipe"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    db_session = get_session()

    try:
        recipe = db_session.query(Recipe).get(recipe_id)
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found'}), 404

        # Verify user has access to this recipe
        user_id = session.get('user_id')
        user_households = db_session.query(Member.HouseholdID).filter(
            Member.UserID == user_id
        ).all()
        user_household_ids = [h[0] for h in user_households]

        recipe_households = db_session.query(Holds.HouseholdID).filter(
            Holds.RecipeID == recipe_id
        ).all()
        recipe_household_ids = [h[0] for h in recipe_households]

        # Check if user has access to at least one household with this recipe
        if not any(hid in user_household_ids for hid in recipe_household_ids):
            return jsonify({'success': False, 'error': 'You do not have access to this recipe'}), 403

        # Get ingredients and servings
        if not recipe.RecipeBody or not isinstance(recipe.RecipeBody, dict):
            return jsonify({'success': False, 'error': 'Recipe has no ingredient data'}), 400

        ingredients = recipe.RecipeBody.get('ingredients', {})
        servings = recipe.RecipeBody.get('serves', 1)

        if not ingredients:
            return jsonify({'success': False, 'error': 'Recipe has no ingredients'}), 400

        # Calculate nutrition
        nutriments_per_serving = calculate_recipe_nutrition(ingredients, servings)

        if not nutriments_per_serving:
            return jsonify({'success': False, 'error': 'Failed to calculate nutrition. Try adding more standard ingredients.'}), 500

        # Update recipe body with nutrition data
        # Need to create a new dict to trigger SQLAlchemy's change detection for JSON columns
        updated_body = dict(recipe.RecipeBody)
        updated_body['nutriments_per_serving'] = nutriments_per_serving
        recipe.RecipeBody = updated_body

        # Mark the column as modified to ensure SQLAlchemy detects the change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(recipe, 'RecipeBody')

        db_session.commit()

        return jsonify({
            'success': True,
            'message': 'Nutrition calculated successfully',
            'nutriments_per_serving': nutriments_per_serving
        })

    except Exception as e:
        db_session.rollback()
        print(f"Error calculating nutrition: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()


@recipes_bp.route('/recipes/add_to_household/<int:recipe_id>', methods=['POST'])
def add_recipe_to_household(recipe_id):
    """Add a recipe to the current household (requires member or admin role)"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    user_id = session.get('user_id')
    current_household_id = session.get('current_household_id')

    if not current_household_id:
        return jsonify({'success': False, 'error': 'No household selected'}), 400

    db_session = get_session()

    try:
        # Verify recipe exists
        recipe = db_session.query(Recipe).get(recipe_id)
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found'}), 404

        # Check if user is admin or member in current household (not viewer/guest)
        member = db_session.query(Member).join(Role).filter(
            Member.UserID == user_id,
            Member.HouseholdID == current_household_id,
            Role.RoleName.in_(['admin', 'member'])
        ).first()

        if not member:
            return jsonify({'success': False, 'error': 'You must be a member to add recipes to this household'}), 403

        # Check if recipe is already in this household
        existing_hold = db_session.query(Holds).filter(
            Holds.HouseholdID == current_household_id,
            Holds.RecipeID == recipe_id
        ).first()

        if existing_hold:
            return jsonify({'success': False, 'error': 'Recipe is already in this household'}), 400

        # Create Holds relationship
        hold = Holds(
            HouseholdID=current_household_id,
            RecipeID=recipe_id
        )
        db_session.add(hold)

        # Create Authors relationship if it doesn't exist
        existing_author = db_session.query(Authors).filter(
            Authors.UserID == user_id,
            Authors.HouseholdID == current_household_id,
            Authors.RecipeID == recipe_id
        ).first()

        if not existing_author:
            author = Authors(
                UserID=user_id,
                HouseholdID=current_household_id,
                RecipeID=recipe_id,
                DateAdded=date.today(),
                IsCustom=not recipe.IsGlobal
            )
            db_session.add(author)

        db_session.commit()

        return jsonify({
            'success': True,
            'message': f'Recipe "{recipe.RecipeName}" added to household'
        })

    except Exception as e:
        db_session.rollback()
        print(f"Error adding recipe to household: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()


@recipes_bp.route('/recipes/remove_from_household/<int:recipe_id>', methods=['POST'])
def remove_recipe_from_household(recipe_id):
    """Remove a recipe from the current household (requires admin role)"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    user_id = session.get('user_id')
    current_household_id = session.get('current_household_id')

    if not current_household_id:
        return jsonify({'success': False, 'error': 'No household selected'}), 400

    db_session = get_session()

    try:
        # Verify recipe exists
        recipe = db_session.query(Recipe).get(recipe_id)
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found'}), 404

        # Check if user is admin in current household
        member = db_session.query(Member).join(Role).filter(
            Member.UserID == user_id,
            Member.HouseholdID == current_household_id,
            Role.RoleName == 'admin'
        ).first()

        if not member:
            return jsonify({'success': False, 'error': 'You must be an admin to remove recipes from this household'}), 403

        # Check if recipe is in this household
        hold = db_session.query(Holds).filter(
            Holds.HouseholdID == current_household_id,
            Holds.RecipeID == recipe_id
        ).first()

        if not hold:
            return jsonify({'success': False, 'error': 'Recipe is not in this household'}), 400

        # Remove Holds relationship
        db_session.delete(hold)

        # Optionally remove Authors relationship for this household
        # (Keep author record if they created it, only remove if they're not the creator)
        author = db_session.query(Authors).filter(
            Authors.HouseholdID == current_household_id,
            Authors.RecipeID == recipe_id
        ).first()

        if author:
            # Only remove author record if recipe is not custom or user didn't create it
            if recipe.IsGlobal or not author.IsCustom:
                db_session.delete(author)

        db_session.commit()

        return jsonify({
            'success': True,
            'message': f'Recipe "{recipe.RecipeName}" removed from household'
        })

    except Exception as e:
        db_session.rollback()
        print(f"Error removing recipe from household: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()