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
    """
    Searches by String in the open food facts data 
    Check root/docs/api for more information
    """
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
    """
    Searches by via String in the USAFood API 
    Check root/docs/api for more information
    """
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
    
#To do 
# Write api throttler
#Implement Loading screen for api Calls
#Find a way to speed up API Calls
#Implement Search by Code 
#