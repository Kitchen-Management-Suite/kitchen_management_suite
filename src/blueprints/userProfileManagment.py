"""
File: calorieTracking.py
File-Path: src/blueprints/calorieTracker.py
Author: Noah Yurasko
Date-Created: 11/12/2025

Description:
    Blueprint for the User Profile Page

Inputs:
    flask request data
    database session

Outputs:
    pages and backend implementation for userProfile
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db.server import get_session
from db.schema import UserProfile

sqlSession = get_session()
flaskSession = session
manage_user_profile_bp = Blueprint("userProfileManagement", __name__)

@manage_user_profile_bp.route("/manage_user_profile", methods = ["GET", "POST"])
def manage_user_profile():
    user_id = flaskSession.get("user_id")

    if not session.get('logged_in'):
        flash('Please login to view recipes', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == "POST":
        print("KAL", request.form["Calorie"])
        try:
            userProfileData = sqlSession.query(UserProfile).filter(UserProfile.UserID == user_id).first()
            sqlSession.commit()
            raise Exception("Test")
        except Exception as ex:
            sqlSession.rollback()
        finally:
            sqlSession.close()

    userProfileData = sqlSession.query(UserProfile).filter(UserProfile.UserID == user_id).first()
    allUnits = {"Metric": 1, "Imperial": 1}

    usableUserProfile = {"Calorie Goal":userProfileData.CalorieGoal,
                         "Height": userProfileData.Height,##Passing data as dict so jira can be used to not repeat html
                         "Weight": userProfileData.Weight,
                         "Allergies": userProfileData.Allergies,
                         "DietaryPreferences": userProfileData.DietaryPreferences,
                         "Units": "Metric"}
    
    print(dir(userProfileData))
     
    return render_template("manage_user_profile.html", userProfileData = usableUserProfile, allUnits = allUnits)