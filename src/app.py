"""
File: app.py
File-Path: src/app.py
Author: Thomas Bruce
Date-Created: 09-29-2025

Description:
    Base of Flask app

Inputs:
    auth blueprint
    db schemas


Outputs:
    serves flask server
    inits db
"""

import os
from flask import Flask, render_template, session, flash
from dotenv import load_dotenv

# load environment variables
load_dotenv()
from db.server import engine, Base, init_database, get_session

# schema imports
from db.schema import adds, authors, holds, household, item, member, pantry, recipe, role, user_nutrition, user_profile, user

# auth blueprint import
from auth import auth_bp

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
            session.commit()
            session.expire_all()

        except Exception as ex:
            session.rollback()
            print("Error in editing macro dumbass",ex)
        finally:
            session.close() 
    
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

    return render_template('calorieTracking.html', nutritionData = nutritionData, session = flaskSession, apiCallTest = trottleApiBy)

##Enter End point here for 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


#To do 
# Pull in new data
# Rewrite api calls for java
# Write api throttler for java
# Design frontend page 
# IF POSSIBLE allow selection of mulitple days
# - This will require automatically checking and creating data for days that dont exist