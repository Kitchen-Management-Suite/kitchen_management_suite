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
from flask import Blueprint, render_template, request, redirect, url_for, session, get_flashed_messages
from db.server import get_session
from db.schema import UserProfile
from flask import flash#look idk why, but for some reason I have to import this seperatley it won't work :/

sqlSession = get_session()
flaskSession = session
manage_user_profile_bp = Blueprint("userProfileManagement", __name__)

@manage_user_profile_bp.route("/manage_user_profile", methods = ["GET", "POST"])
def manage_user_profile():
    user_id = flaskSession.get("user_id")
    if not session.get('logged_in'):
        flash('Please login to view pantry', 'error')
        return redirect(url_for('auth.login'))
    
    userProfileData = sqlSession.query(UserProfile).filter(UserProfile.UserID == user_id).first()
    #NEED TO HANDLE CASE WHERE THERE IS NO PROFILE YET CREATED
    if request.method == "POST":
        print("KAL", request.form["Calorie"])
        try:#NEED TO DO SANITIZATION HERE
            userProfileData.CalorieGoal =  request.form["Calorie"] if "Calorie" in request.form else userProfileData.CalorieGoal
            userProfileData.Height =  request.form["Height"] if "Height" in request.form else userProfileData.Height
            userProfileData.Weight =  request.form["Weight"] if "Weight" in request.form else userProfileData.Weight
            userProfileData.DietaryPreferences =  request.form["DietaryPreferences"] if "DietaryPreferences" in request.form else userProfileData.DietaryPreferences
            userProfileData.Allergies =  request.form["Allergies"] if "Allergies" in request.form else userProfileData.Allergies
            sqlSession.commit()
        except Exception as ex:
            print("EXCEPTION")
            print(ex)
            flash('Error In Updating Profile', 'error')
            sqlSession.rollback()

            return redirect(url_for('index'))
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