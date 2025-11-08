"""
File: calorieTracking.py
File-Path: src/blueprints/calorieTracker.py
Author: Rohan Plante
Date-Created: 11/5/2025 - Updated 11/7/2025

Description:
    Blueprint for the Calorie Tracking page

Inputs:
    flask request data
    database session

Outputs:
    pages for calorie Tracking
"""
#NOTE: Most of information passing for calorieTracking is done via forms and http requests
#I realized at the end that I could be passing information through browsers with URL query parametes
#In the future if I clean up this code I will swtich all to that, but for rn it all works
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from db.server import get_session
from db.schema import user_nutrition
from sqlalchemy import and_, func
from datetime import datetime
from helpers.api_helper import searchByCode, searchRawIntredient, searchByStr

sqlSession = get_session()
flaskSession = session

calorie_tracker_bp = Blueprint('caloreTracker', __name__)

#This is the page the user is routed to when searching for food
@calorie_tracker_bp.route("/meal_item_search", methods = ["GET", "POST"])
def meal_item_search():
    if not session.get('logged_in'):
        flash('Please log in to track calories.', 'error')
        return redirect(url_for('auth.login'))
    MealType = request.args.get("MealType")
    return render_template("meal_item_search.html", MealType = MealType)

#This endpoint is used to make the API call and redirct the user to the same html page with the loaded content
@calorie_tracker_bp.route("/api_search_item_name", methods = ["GET", "POST"])
def api_search_item_name():

    if not session.get('logged_in'):
        flash('Please log in to track calories.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == "POST":
        itemBeingSearched = request.form["search_input"]
        MealType = request.form["MealType"]
        print(f"Calling backend API - searching by name for {itemBeingSearched}")
        response = searchByStr(itemBeingSearched)#searchByStr(itemBeingSearched, page_size = 10)#We should do some sanitzation here BTW

        if response == -1:
            #Error is handled and flashed in openfoodapi.py 
            return render_template("meal_item_search.html")
        
        if response == None:
            flash(f"Could not find '{itemBeingSearched}' in in openfoodfacts", "error")
            return render_template("meal_item_search.html")
        
    return render_template("meal_item_search.html", productResults = response["products"], userquery = itemBeingSearched, MealType = MealType)

#Adds entryToUserNutrition
def addToLog(UserNutrition):
    try:
        sqlSession.add(UserNutrition)
        sqlSession.commit()
        sqlSession.expire_all()

    except Exception as ex:
        sqlSession.rollback()
        flash("Error in writing to database", "error")
        print("Error in session dumbass",ex)
    finally:
        sqlSession.close() 

#Default display page for calorie Tracking  
@calorie_tracker_bp.route('/calorieTracking', methods = ["GET", "POST"])
def calorieTracking():#KNOWN BUG - reloading this page after adding an item will add it to the database twice :/ fix later
    user_id = flaskSession.get("user_id")
    
    if not user_id:### Need to unit test
        flash("User Not Found", "error")
        return render_template('index')
    
    now = datetime.now() 
    date = now.date()
    time = now.time()
    if request.method == "POST":##Handles route for when new food entry is added
        try:
            allItemData = request.form["itemName"]
            newNutritionEntry = user_nutrition.UserNutrition(
                UserID = user_id,
                Date = date,
                Time = time,
                # ItemName = request.form['itemName'],
                CaloriesConsumed = request.form["itemKCal"],
                Protein = request.form["itemProtein"],
                Carbs = request.form["itemCarbs"],
                Fat = request.form["itemFat"],
                Fiber = request.form["itemFiber"],
                Sugar = request.form["itemSugar"],
                Sodium = request.form["itemSodium"],
                # MealType = request.form["MealType"]
            )
            addToLog(newNutritionEntry)
        except:
            flash("Error in adding item to log", "error")
            #Log/Handle Here
            print(ex)
    dashBoardValues = {"Calories": 0, "Carbs": 0, "Protein": 0, "Fat": 0} #Setting default values
    try:
        #Will be seperating out nutrition data into breakfast lunch and dinner once db/monkeyType is updated
        nD = user_nutrition.UserNutrition
        nutritionData = sqlSession.query(nD).filter(nD.UserID == session["user_id"]).filter(nD.Date == date).all()
        if not len(nutritionData) == 0:
            for entry in nutritionData:
                dashBoardValues["Calories"] += entry.CaloriesConsumed
                dashBoardValues["Carbs"] += entry.Carbs
                dashBoardValues["Protein"] += entry.Protein
                dashBoardValues["Fat"] += entry.Fat


    except Exception as ex:
        flash("Error in database query", "error")
        print("ERROR HERE")
        print(ex)
        
    if not nutritionData: 
        print("No User nutrition data retrieved")

    print("TESTING")
    print(dashBoardValues)
    return render_template('calorieTracking.html', 
                           dashBoardValues = dashBoardValues, 
                           date = date,
                           session = flaskSession, 
                           mealItemSearchUrl = "/meal_item_search")