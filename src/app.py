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

#API Imports
from openfoodapi import searchByCode, searchByStr, trottleApiBy 

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# initialize database tables
with app.app_context():
    print("initializing database...")
    init_database()

#Dstinguishing sessions for sqlAlchemy & flask 
sqlSession = get_session()
flaskSession = session

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
    if flaskSession.get('logged_in'):
        return render_template("index.html")
    else:
        return render_template("public.html")
    
def editMacro(UserNutrition, macroType, newVal):
        try:
            #setattr(MyClass, attribute_name_vaxriable, attribute_value)
            setattr(UserNutrition, macroType, newVal)
            sqlSession.commit()
            sqlSession.expire_all()

        except Exception as ex:
            sqlSession.rollback()
            print("Error in editing macro dumbass",ex)
        finally:
            sqlSession.close() 
    
@app.route('/calorieTracking')
def calorieTracking():
    user_id = flaskSession.get("user_id")
    
    if not user_id:
        flash("User Not Found", "error")
        return render_template('index')

    nutritionData = sqlSession.query(user_nutrition.UserNutrition).filter(user_nutrition.UserNutrition.UserID == session["user_id"]).first()

    if not nutritionData: 
        flash("No user nutrition data found, populating default values", "warning")
        return render_template('index')

    return render_template('calorieTracking.html', nutritionData = nutritionData, session = flaskSession)

##Enter End point here for 

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

@app.route("/switch_household/<int:household_id>")
def switch_household(household_id):
    """Switch the current household for the user session"""
    if not session.get('logged_in'):
        flash('Please log in to switch households.', 'error')
        return redirect(url_for('auth.login'))
    
    households = get_user_households()
    household_ids = [h.HouseholdID for h in households]
    
    if household_id in household_ids:
        set_current_household_id(household_id)
        flash('Household switched successfully', 'success')
    else:
        flash('You do not have access to this household', 'error')
    
    return redirect(request.referrer)

@app.route("/household/manage")
def manage_household():
    """Handle household management route"""
    if not session.get('logged_in'):
        flash('Please log in to manage households.', 'error')
        return redirect(url_for('auth.login'))

    # NEED TO IMPLEMENT HOUSEHOLD CREATION AND JOIN FUNCTIONALITY
    return render_template('manage_household.html')

@app.route("/meal_item_search")
def meal_item_search():
    if not session.get('logged_in'):
        flash('Please log in to track calories.', 'error')
        return redirect(url_for('auth.login'))
    print("TEST")
    return render_template("meal_item_search.html")

@app.route("/api_search_item_name", methods = ["GET", "POST"])
def api_search_item_name():
    if not session.get('logged_in'):
        flash('Please log in to track calories.', 'error')
        return redirect(url_for('auth.login'))
    if request.method == "POST":
        itemBeingSearched = request.form["search_input"]
        print(f"Calling backend API - searching by name for {itemBeingSearched}")
        response = searchByStr(itemBeingSearched, page_size = 10)#We should do some sanitzation here BTW
        if response == -1: 
            return render_template("meal_item_search.html")
        # print(response)
        print(len(response["products"]))
        
    return render_template("meal_item_search.html", productResults = response["products"], userquery = itemBeingSearched)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



#To do 
# Rewrite api calls for java
# Write api throttler for java
# Write conditionals for loading calorite track page
# Write second (VERY BASIC) search page for info meals
# Write the ability to pull in anything else necessary (recipies etc)
# IF POSSIBLE allow selection of mulitple days
# - This will require automatically checking and creating data for days that dont exist