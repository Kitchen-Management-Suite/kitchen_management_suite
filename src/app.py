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
    inject_navbar_context
)

# import blueprints
from blueprints.auth import auth_bp
from blueprints.recipes import recipes_bp

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# initialize database tables
with app.app_context():
    print("initializing database...")
    init_database()

# register auth blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(recipes_bp)

# register navbar w/ context processor (inject w/ existing variables)
# refer to navbar_helper.py
@app.context_processor
def inject_navbar():
    """Inject navbar data into templates"""
    return inject_navbar_context()

@app.route("/")
def index():
    """handle index route"""
    if session.get('logged_in'):
        return render_template("index.html")
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

@app.route("/account")
def account():
    """handle account route"""
    if not session.get('logged_in'):
        flash('Please log in to access your account.', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template("account.html")

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
    
    return redirect(url_for('manage_household'))

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
