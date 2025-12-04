"""
File: app.py
File-Path: src/app.py
Author: Thomas Bruce, Rohan Plante
Date-Created: 09-29-2025

Description:
    Base of Flask app

Inputs:
    flask blueprints
    db schemas


Outputs:
    serves flask server
    inits db
"""

import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from dotenv import load_dotenv

# load environment variables
load_dotenv()

from db.server import engine, Base, init_database, get_session

# schema imports
from db.schema import adds, authors, holds, household, item, member, pantry, recipe, role, user_nutrition, user_profile, user

# helper imports
from helpers.navbar_helper import (
    set_current_household_id,
    get_user_households,
    get_user_households_with_roles,
    inject_navbar_context,
    get_current_user_role
)

# import blueprints
from blueprints.auth import auth_bp
from blueprints.recipes import recipes_bp
from blueprints.calorieTracker import calorie_tracker_bp
from blueprints.pantry import pantry_bp
from blueprints.userProfileManagment import manage_user_profile_bp
from blueprints.settings import settings_bp

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# initialize database tables
with app.app_context():
    print("initializing database...")
    init_database()

#Dstinguishing sessions for sqlAlchemy & flask 
sqlSession = get_session()
flaskSession = session

# register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(recipes_bp)
app.register_blueprint(pantry_bp)
app.register_blueprint(calorie_tracker_bp)
app.register_blueprint(manage_user_profile_bp)
app.register_blueprint(settings_bp)


# register navbar w/ context processor (inject w/ existing variables)
# refer to navbar_helper.py
@app.context_processor
def inject_navbar():
    """Inject navbar data into templates"""
    return inject_navbar_context()

@app.route("/")
def index():
    """handle index route"""
    if flaskSession.get('logged_in'):
        user_id = session.get('user_id')
        current_household_id = session.get('current_household_id')
        db_session = get_session()

        try:
            from db.schema.household import Household
            from db.schema.member import Member
            from db.schema.pantry import Pantry
            from db.schema.adds import Adds
            from db.schema.item import Item
            from db.schema.holds import Holds
            from db.schema.authors import Authors
            from db.schema.recipe import Recipe
            from sqlalchemy import func, distinct, and_
            from datetime import datetime, timedelta
            from collections import defaultdict

            # Initialize metrics
            metrics = {
                'total_households': 0,
                'current_household': None,
                'pantry_items_count': 0,
                'household_recipes_count': 0,
                'user_recipes_count': 0,
                'recent_activity': [],
                'household_members_count': 0,
                'suggested_recipes': [],
                'expiring_soon': [],
                'shopping_list': [],
                'top_contributors': []
            }

            # Get total households user is part of
            user_households = db_session.query(Member).filter(
                Member.UserID == user_id
            ).all()
            metrics['total_households'] = len(user_households)

            # If no current household is set but user has households, set the first one
            if not current_household_id and user_households:
                current_household_id = user_households[0].HouseholdID
                session['current_household_id'] = current_household_id

            if current_household_id:
                # Get current household details
                current_household = db_session.query(Household).get(current_household_id)
                metrics['current_household'] = current_household

                # Get household member count
                members_count = db_session.query(func.count(Member.MemberID)).filter(
                    Member.HouseholdID == current_household_id
                ).scalar()
                metrics['household_members_count'] = members_count or 0

                # Get pantry statistics
                pantry = db_session.query(Pantry).filter(
                    Pantry.HouseholdID == current_household_id
                ).first()

                if pantry:
                    # Count unique items in pantry
                    unique_items = db_session.query(func.count(distinct(Adds.ItemID))).filter(
                        Adds.PantryID == pantry.PantryID
                    ).scalar()
                    metrics['pantry_items_count'] = unique_items or 0

                    # Get recent activity (additions from all members in last 14 days)
                    from db.schema.user import User
                    fourteen_days_ago = datetime.now().date() - timedelta(days=14)
                    recent_activity = db_session.query(
                        User.Username,
                        Item.ItemName,
                        Adds.Quantity,
                        Adds.Unit,
                        Adds.ItemInDate
                    ).join(Item).join(User).filter(
                        Adds.PantryID == pantry.PantryID,
                        Adds.ItemInDate >= fourteen_days_ago
                    ).order_by(Adds.ItemInDate.desc()).limit(10).all()

                    metrics['recent_activity'] = [
                        {
                            'user': activity.Username,
                            'item': activity.ItemName,
                            'quantity': activity.Quantity,
                            'unit': activity.Unit or 'pieces',
                            'date': activity.ItemInDate,
                            'days_ago': (datetime.now().date() - activity.ItemInDate).days
                        } for activity in recent_activity
                    ]

                    # Get items added more than 60 days ago (potentially expiring)
                    sixty_days_ago = datetime.now().date() - timedelta(days=60)
                    old_items = db_session.query(
                        Item.ItemName,
                        func.min(Adds.ItemInDate).label('oldest_date'),
                        func.sum(Adds.Quantity).label('total_qty'),
                        Adds.Unit
                    ).join(Adds).filter(
                        Adds.PantryID == pantry.PantryID,
                        Adds.ItemInDate < sixty_days_ago
                    ).group_by(Item.ItemName, Adds.Unit).limit(8).all()

                    metrics['expiring_soon'] = [
                        {
                            'name': item.ItemName,
                            'quantity': item.total_qty,
                            'unit': item.Unit or 'pieces',
                            'days_old': (datetime.now().date() - item.oldest_date).days
                        } for item in old_items
                    ]

                    # Build pantry items dict for recipe matching
                    pantry_items_raw = db_session.query(
                        Item.ItemName,
                        Adds.Quantity,
                        Adds.Unit
                    ).join(Adds).filter(
                        Adds.PantryID == pantry.PantryID
                    ).all()

                    pantry_items_dict = defaultdict(list)
                    for item_name, qty, unit in pantry_items_raw:
                        pantry_items_dict[item_name.lower()].append((qty, unit or 'pieces'))

                    # Get top 3 recipes from household that match pantry
                    household_recipe_ids = db_session.query(Holds.RecipeID).filter(
                        Holds.HouseholdID == current_household_id
                    ).all()
                    household_recipe_ids = [r[0] for r in household_recipe_ids]

                    if household_recipe_ids:
                        household_recipes = db_session.query(Recipe).filter(
                            Recipe.RecipeID.in_(household_recipe_ids)
                        ).limit(10).all()

                        # Score recipes based on pantry match
                        scored_recipes = []
                        for recipe in household_recipes:
                            if recipe.RecipeBody and 'ingredients' in recipe.RecipeBody:
                                ingredients = recipe.RecipeBody['ingredients']
                                total_ingredients = len(ingredients)
                                matched = 0

                                for ing_key, ing_data in ingredients.items():
                                    if isinstance(ing_data, dict):
                                        ing_name = ing_data.get('id', ing_key).replace('-', ' ').lower()
                                        if ing_name in pantry_items_dict:
                                            matched += 1

                                if total_ingredients > 0:
                                    match_score = int((matched / total_ingredients) * 100)
                                    scored_recipes.append({
                                        'recipe': recipe,
                                        'score': match_score,
                                        'matched': matched,
                                        'total': total_ingredients
                                    })

                        # Sort by score and take top 3
                        scored_recipes.sort(key=lambda x: x['score'], reverse=True)
                        metrics['suggested_recipes'] = scored_recipes[:3]

                        # Generate shopping list from top recipe (if match < 100%)
                        if scored_recipes and scored_recipes[0]['score'] < 100:
                            top_recipe = scored_recipes[0]['recipe']
                            missing_items = []

                            if top_recipe.RecipeBody and 'ingredients' in top_recipe.RecipeBody:
                                for ing_key, ing_data in top_recipe.RecipeBody['ingredients'].items():
                                    if isinstance(ing_data, dict):
                                        ing_name = ing_data.get('id', ing_key).replace('-', ' ')
                                        if ing_name.lower() not in pantry_items_dict:
                                            missing_items.append({
                                                'name': ing_name.title(),
                                                'amount': ing_data.get('amount', ''),
                                                'unit': ing_data.get('unit', ''),
                                                'recipe': top_recipe.RecipeName
                                            })

                            metrics['shopping_list'] = missing_items[:6]

                    # Get top contributors (users who added most items in last 30 days)
                    thirty_days_ago = datetime.now().date() - timedelta(days=30)
                    top_contributors = db_session.query(
                        User.Username,
                        func.count(Adds.AddsID).label('additions_count')
                    ).join(User).filter(
                        Adds.PantryID == pantry.PantryID,
                        Adds.ItemInDate >= thirty_days_ago
                    ).group_by(User.Username).order_by(func.count(Adds.AddsID).desc()).limit(5).all()

                    metrics['top_contributors'] = [
                        {
                            'username': contrib.Username,
                            'count': contrib.additions_count
                        } for contrib in top_contributors
                    ]

                # Get household recipe count
                household_recipe_count = db_session.query(func.count(Holds.RecipeID)).filter(
                    Holds.HouseholdID == current_household_id
                ).scalar()
                metrics['household_recipes_count'] = household_recipe_count or 0

            # Get user's total authored recipes
            user_recipe_count = db_session.query(func.count(distinct(Authors.RecipeID))).filter(
                Authors.UserID == user_id
            ).scalar()
            metrics['user_recipes_count'] = user_recipe_count or 0

            return render_template("index.html", metrics=metrics)

        except Exception as e:
            print(f"Error loading home metrics: {e}")
            return render_template("index.html", metrics=None)
        finally:
            db_session.close()
    else:
        return render_template("public.html")

@app.route("/pantry")
def pantry():
    """handle pantry route"""
    if not session.get('logged_in'):
        flash('Please log in to access the pantry.', 'error')
        return redirect(url_for('auth.login'))
    
    # check if user is in any households
    households = get_user_households()
    if not households:
        flash('You need to join a household first.', 'error')
        return redirect(url_for('index'))

    return render_template("pantry.html")

@app.route("/recipes")
def recipes():
    """handle recipes route"""
    if not session.get('logged_in'):
        flash('Please log in to access the recipes.', 'error')
        return redirect(url_for('auth.login'))

    return render_template(url_for('recipes.recipes'))

@app.route("/settings")
def account():
    """handle route to settings"""
    return redirect(url_for('settings.settings'))

@app.route("/switch_household/<int:household_id>", methods=['GET', 'POST'])
def switch_household(household_id):
    """Switch the current household for the user session"""
    if not session.get('logged_in'):
        flash('Please log in to switch households.', 'error')
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    db_session = get_session()

    try:
        from db.schema.member import Member

        #verify user is a member of this household
        member = db_session.query(Member).filter(
            Member.UserID == user_id,
            Member.HouseholdID == household_id
        ).first()

        if member:
            set_current_household_id(household_id)
            flash('Household switched successfully', 'success')
        else:
            flash('You do not have access to this household', 'error')
    except Exception as e:
        flash(f'Error switching household: {str(e)}', 'error')
    finally:
        db_session.close()

    # redirect back to the page the user came from, or to index if no referrer
    next_url = request.args.get('next') or request.referrer or url_for('index')
    return redirect(next_url)

@app.route("/household/manage")
def manage_household():
    """Handle household management route"""
    if not session.get('logged_in'):
        flash('Please log in to manage households.', 'error')
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    db_session = get_session()
    
    try:
        #get user households with roles
        from db.schema.household import Household
        from db.schema.member import Member
        from db.schema.role import Role
        
        user_households_data = db_session.query(
            Household,
            Member,
            Role
        ).join(
            Member, Household.HouseholdID == Member.HouseholdID
        ).join(
            Role, Member.RoleID == Role.RoleID
        ).filter(
            Member.UserID == user_id
        ).all()
        
        #format data for template
        user_households = []
        for household, member, role in user_households_data:
            user_households.append({
                'HouseholdID': household.HouseholdID,
                'HouseholdName': household.HouseholdName,
                'Role': role.RoleName,
                'RoleID': role.RoleID
            })
        
        current_household_id = session.get('current_household_id')
        
        return render_template('manage_household.html',
                             user_households=user_households,
                             current_household_id=current_household_id)
    
    except Exception as e:
        flash(f'Error loading households: {str(e)}', 'error')
        return render_template('manage_household.html',
                             user_households=[],
                             current_household_id=None)
    finally:
        db_session.close()

@app.route("/household/create", methods=['GET', 'POST'])
def create_household():
    """Create a new household"""
    if not session.get('logged_in'):
        flash('Please log in to create a household.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        user_id = session.get('user_id')
        household_name = request.form.get('household_name', '').strip()
        
        if not household_name:
            flash('Household name is required.', 'error')
            return redirect(url_for('manage_household'))

        db_session = get_session()
        try:
            from db.schema.household import Household
            from db.schema.member import Member
            from db.schema.role import Role
            from db.schema.pantry import Pantry
            
            #check if household name already exists
            existing_household = db_session.query(Household).filter(
                Household.HouseholdName == household_name
            ).first()
            
            if existing_household:
                flash('A household with this name already exists.', 'error')
                return redirect(url_for('manage_household'))
            
            #get Owner role
            owner_role = db_session.query(Role).filter(Role.RoleName == 'Owner').first()
            if not owner_role:
                flash('Owner role not found in database.', 'error')
                return redirect(url_for('manage_household'))
            
            #create new household
            new_household = Household(HouseholdName=household_name)
            db_session.add(new_household)
            db_session.flush()
            
            #create pantry for the household
            new_pantry = Pantry(HouseholdID=new_household.HouseholdID)
            db_session.add(new_pantry)
            
            #add user as member with owner role
            new_member = Member(
                UserID=user_id,
                HouseholdID=new_household.HouseholdID,
                RoleID=owner_role.RoleID
            )
            db_session.add(new_member)
            
            db_session.commit()
            
            #set as current household
            session['current_household_id'] = new_household.HouseholdID
            
            flash(f'Household "{household_name}" created successfully!', 'success')
            return redirect(url_for('manage_household'))
            
        except Exception as e:
            db_session.rollback()
            flash(f'Error creating household: {str(e)}', 'error')
            return redirect(url_for('manage_household'))
        finally:
            db_session.close()
    
    return redirect(url_for('manage_household'))

@app.route("/household/join", methods=['GET', 'POST'])
def join_household():
    """Join an existing household"""
    if not session.get('logged_in'):
        flash('Please log in to join a household.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        user_id = session.get('user_id')
        join_code = request.form.get('join_code', '').strip()
        
        if not join_code:
            flash('Household name is required.', 'error')
            return redirect(url_for('manage_household'))

        db_session = get_session()
        try:
            from db.schema.household import Household
            from db.schema.member import Member
            from db.schema.role import Role
            from sqlalchemy import func
            
            #try to find household by name 
            join_code_clean = join_code.strip()
            household = db_session.query(Household).filter(
                func.lower(Household.HouseholdName) == func.lower(join_code_clean)
            ).first()
            
            if not household:
                flash(f'Household "{join_code_clean}" not found. Please check the name and try again.', 'error')
                return redirect(url_for('manage_household'))
            
            #check if user is already a member
            existing_member = db_session.query(Member).filter(
                Member.UserID == user_id,
                Member.HouseholdID == household.HouseholdID
            ).first()
            
            if existing_member:
                flash('You are already a member of this household.', 'error')
                return redirect(url_for('manage_household'))
            
            #get Member role
            member_role = db_session.query(Role).filter(Role.RoleName == 'Member').first()
            if not member_role:
                flash('Member role not found in database.', 'error')
                return redirect(url_for('manage_household'))
            
            #add user as member
            new_member = Member(
                UserID=user_id,
                HouseholdID=household.HouseholdID,
                RoleID=member_role.RoleID
            )
            db_session.add(new_member)
            db_session.commit()
            
            #set as current household if user has no current household
            if not session.get('current_household_id'):
                session['current_household_id'] = household.HouseholdID
            
            flash(f'Successfully joined "{household.HouseholdName}"!', 'success')
            return redirect(url_for('manage_household'))
            
        except Exception as e:
            db_session.rollback()
            flash(f'Error joining household: {str(e)}', 'error')
            return redirect(url_for('manage_household'))
        finally:
            db_session.close()
    
    return redirect(url_for('manage_household'))

@app.route("/household/settings")
def household_settings():
    """Handle household settings route - admin only"""
    if not session.get('logged_in'):
        flash('Please log in to access household settings.', 'error')
        return redirect(url_for('auth.login'))

    # Check if user is admin in current household
    user_role = get_current_user_role()
    if user_role != 'admin':
        flash('You must be an admin to access household settings.', 'error')
        return redirect(url_for('index'))

    # Check if user is in any households
    households = get_user_households()
    if not households:
        flash('You need to join a household first.', 'error')
        return redirect(url_for('index'))

    return render_template('household_settings.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

#To do 
# Write api throttler for java
# Write conditionals for loading calorite track page
#Finish styling very basic search page
# # Write the ability to pull in anything else necessary (recipies etc)
# IF POSSIBLE allow selection of mulitple days
# - This will require automatically checking and creating data for days that dont exist