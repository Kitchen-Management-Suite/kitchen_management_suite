"""
File: fopenfoodapi.py
File-Path: src/openfoodapi.py
Author: Noah Yurasko
Date-Created: 11/5/2025

Description:
    contains all the innerworkings of api calls to openfood facts api
    including rate throttling

Inputs:
    Active flask session & dot env file with the openfoodfacts_api_useragent attribute 

Outputs:
    functions to be called by app.py during the necessary course of searching for food items
"""

import os
from dotenv import load_dotenv
from flask import session as flaskSession
from flask import flash
import time
import openfoodfacts
import json
import requests

openfoodfacts_api_useragent = os.getenv('openfoodfacts_api_useragent', 'openfoodfacts_api_useragent')
api = openfoodfacts.API(user_agent=openfoodfacts_api_useragent, timeout = 30)

def trottleApiBy(apiLimit):
    """
    Returns a float value which is used to trottle api connections
    """
    
    if not ("lastApiSearch" in flaskSession):
        flaskSession["lastApiSearch"] = time.time()
        return 0
    timeSince = time.time() - flaskSession["lastApiSearch"]

    if timeSince > 60:
        return 0

    expectedTimeTilEnd = timeSince * (apiLimit-1) 


    flaskSession["lastApiSearch"] == time.time()
    print(timeSince)
    
    print(type(flaskSession))
    return 1
    # if flaskSession

def searchByStr(searchText, **kwargs):#Will Need to sanitize search later
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    defaultFields = ["generic_name_en", 
                     "image_front_small_url",
                     "ingredients_text_en", 
                     "no_nutrition_data", 
                     "nutrition_data",
                      "obsolete" ]
    page_size = kwargs.get("page_size", 100)## We should move this into the try loop for production
    page = kwargs.get("page", 1)
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
        with open("jasonTempSave", "w") as f:
            json.dump(responseAsJson, f, indent=4) 
        return responseAsJson
    except Exception as ex:
        print("Exception in API Call")#We need to handle errors better
        flash(ex, "error")

        return -1

def searchByCode(code, **kwargs):

    try:
        rtn = api.product.get(code, fields=["code", "product_name"])
        return rtn
    except:
        print("Exception in API Call")
        return -1
    
code = "3017620422003"
