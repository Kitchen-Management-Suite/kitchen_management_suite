"""
File: fopenfoodapi.py
File-Path: src/openfoodapi.py
Author: Noah Yurasko
Date-Created: 11/5/2025

Description:
    contains all the innerworkings of api calls to openfoodfacts api
    Doucmentation found in docs/api
    including rate throttling [TBD]

Inputs:
    Active flask session & dot env file with the openfoodfacts_api_useragent attribute 

Outputs:
    functions to be called by app.py during the necessary course of searching for food items
"""

import os
from dotenv import load_dotenv
from flask import session as flaskSession
from flask import flash
# import time
import openfoodfacts
import json
import requests

openfoodfacts_api_useragent = os.getenv('openfoodfacts_api_useragent', None)
USDAApiKey = os.getenv("USDAApiKey", None)
api = openfoodfacts.API(user_agent=openfoodfacts_api_useragent, timeout = 30)##Consider getting rid of this and switching all to requests

if openfoodfacts_api_useragent == None:
    raise Exception("Could not find openFoodFacts api useragent")

if USDAApiKey == None:
    raise Exception("Could not find USDA api key")

# def trottleApiBy(apiLimit):#Still being implemented
#     """
#     Returns a float value which is used to trottle api connections
#     """
    
#     if not ("lastApiSearch" in flaskSession):
#         flaskSession["lastApiSearch"] = time.time()
#         return 0
#     timeSince = time.time() - flaskSession["lastApiSearch"]

#     if timeSince > 60:
#         return 0

#     expectedTimeTilEnd = timeSince * (apiLimit-1) 


#     flaskSession["lastApiSearch"] == time.time()
#     print(timeSince)
    
#     print(type(flaskSession))
#     return 0
#     # if flaskSession

def searchByStr(searchText, **kwargs):#Will Need to sanitize search later#SUCH AS CHECK FOR EMPTY STRINGS, 
    #Emptry strings from openfoodfacts prevent writing to database
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    defaultFields = ["generic_name_en", #Not implemented
                     "image_front_small_url",
                     "ingredients_text_en", 
                     "no_nutrition_data", 
                     "nutrition_data",
                      "obsolete" ]
    params = {
        "search_terms": searchText,
        "search_simple": 1, 
        "json": 1,
        "page": kwargs.get("page", 1),
        "page_size": kwargs.get("page_size", 100),
        "complete": 1,
        "country": "united-states"
        # "countries": "united-states"
    } 
    try: 
        response = requests.get(url, params=params)
        responseAsJson = response.json()
        # with open("jasonTempSave", "w") as f:#Used for testing somtimes
        #     json.dump(responseAsJson, f, indent=4) 
        return responseAsJson
    except Exception as ex:
        print("Exception in API Call")#We need to handle errors better
        flash(ex, "error")
        return -1

def searchByCode(code, **kwargs):#Deprecated, need to change
    try:
        # rtn = api.product.get(code, fields=["code", "product_name"])
        return -1
    except:
        print("Exception in API Call")
        return -1

def searchRawIngredient(name, **kwargs):
    try: 
        url =  "https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {
            "query": name,
            "api_key": USDAApiKey,
            "pageNumber": kwargs.get("page", 1),
            "pageSize": kwargs.get("page_size", 100),
        }

        rtn = requests.get(url, params=params)
        responseAsJson = rtn.json()
        return responseAsJson
    except Exception as ex: 
        print("Exception in USDA Api call")
        print(ex)
        return -1
    
def calculate_recipe_nutrition(ingredients, servings=1):
    """
    Calculate nutrition facts for a recipe based on its ingredients.

    Args:
        ingredients: Dict of ingredients in format {key: {amount, unit, id}}
        servings: Number of servings the recipe makes

    Returns:
        Dict with nutrition data per serving, or None if calculation fails
    """
    total_nutrition = {
        'energy-kcal': 0,
        'fat': 0,
        'carbohydrates': 0,
        'fiber': 0,
        'sugars': 0,
        'proteins': 0,
        'sodium': 0,
        'saturated-fat': 0
    }

    successful_matches = 0
    total_ingredients = len(ingredients)

    for ing_key, ing_data in ingredients.items():
        if not isinstance(ing_data, dict):
            continue

        ing_name = ing_data.get('id', ing_key).replace('-', ' ')
        amount = float(ing_data.get('amount', 0))
        unit = ing_data.get('unit', '')

        if amount <= 0:
            continue

        # Try OpenFoodFacts first
        try:
            search_result = searchByStr(ing_name, page_size=5)
            if search_result != -1 and 'products' in search_result and len(search_result['products']) > 0:
                product = search_result['products'][0]
                nutriments = product.get('nutriments', {})

                if nutriments:
                    # Convert amount to grams for calculation (simplified conversion)
                    amount_in_grams = _convert_to_grams(amount, unit)

                    # Get nutriments per 100g and scale to our amount
                    scale_factor = amount_in_grams / 100.0

                    for nutrient in total_nutrition.keys():
                        nutrient_value = nutriments.get(nutrient, 0) or nutriments.get(f'{nutrient}_100g', 0)
                        if nutrient_value:
                            total_nutrition[nutrient] += nutrient_value * scale_factor

                    successful_matches += 1
                    continue
        except Exception as e:
            print(f"OpenFoodFacts lookup failed for {ing_name}: {e}")

        # Fallback to USDA API
        try:
            usda_result = searchRawIngredient(ing_name, page_size=5)
            if usda_result != -1 and 'foods' in usda_result and len(usda_result['foods']) > 0:
                food = usda_result['foods'][0]
                nutrients = food.get('foodNutrients', [])

                amount_in_grams = _convert_to_grams(amount, unit)
                scale_factor = amount_in_grams / 100.0

                # Map USDA nutrient IDs to our keys
                nutrient_mapping = {
                    'Energy': 'energy-kcal',
                    'Total lipid (fat)': 'fat',
                    'Carbohydrate, by difference': 'carbohydrates',
                    'Fiber, total dietary': 'fiber',
                    'Sugars, total including NLEA': 'sugars',
                    'Protein': 'proteins',
                    'Sodium, Na': 'sodium',
                    'Fatty acids, total saturated': 'saturated-fat'
                }

                for nutrient in nutrients:
                    nutrient_name = nutrient.get('nutrientName', '')
                    nutrient_value = nutrient.get('value', 0)

                    if nutrient_name in nutrient_mapping:
                        key = nutrient_mapping[nutrient_name]
                        # USDA values are per 100g
                        total_nutrition[key] += nutrient_value * scale_factor

                successful_matches += 1
        except Exception as e:
            print(f"USDA lookup failed for {ing_name}: {e}")

    # If we couldn't match any ingredients, return None
    if successful_matches == 0:
        return None

    # Calculate per-serving nutrition
    nutriments_per_serving = {}
    for key, value in total_nutrition.items():
        nutriments_per_serving[key] = value / max(servings, 1)

    return nutriments_per_serving


def _convert_to_grams(amount, unit):
    """
    Convert ingredient amounts to grams for nutrition calculation.
    This is a simplified conversion - real conversions depend on ingredient density.
    """
    unit = unit.lower()

    # Volume to grams (using water density as approximation)
    volume_conversions = {
        'cup': 240,
        'cups': 240,
        'tbsp': 15,
        'tablespoon': 15,
        'tablespoons': 15,
        'tsp': 5,
        'teaspoon': 5,
        'teaspoons': 5,
        'ml': 1,
        'milliliter': 1,
        'milliliters': 1,
        'liter': 1000,
        'liters': 1000,
        'l': 1000,
        'fl oz': 30,
        'fluid ounce': 30,
        'fluid ounces': 30
    }

    # Weight to grams
    weight_conversions = {
        'g': 1,
        'gram': 1,
        'grams': 1,
        'kg': 1000,
        'kilogram': 1000,
        'kilograms': 1000,
        'oz': 28.35,
        'ounce': 28.35,
        'ounces': 28.35,
        'lb': 453.59,
        'pound': 453.59,
        'pounds': 453.59
    }

    # Check weight conversions first (more accurate)
    if unit in weight_conversions:
        return amount * weight_conversions[unit]

    # Check volume conversions
    if unit in volume_conversions:
        return amount * volume_conversions[unit]

    # Default: assume pieces/counts, use average weight of 100g per piece
    if unit in ['piece', 'pieces', 'whole', 'clove', 'cloves', 'to taste', '']:
        return amount * 100

    # Unknown unit, default to 100g
    return amount * 100


#To do
# Write api throttler
# Write conditionals for loading calorite track page
#Finish styling very basic search page
# # Write the ability to pull in anything else necessary (recipies etc)
# IF POSSIBLE allow a view of multiple days
#Running Bugs:
#Reloading the page after adding an item will add it twice
#its with empty strings cannot be added to the database