"""
Use cases:
Search for food by name
Search for food by barcode
- Hande Rate Limits 
- Cache recent data?
"""

import os
from dotenv import load_dotenv
from flask import session as flaskSession
import openfoodfacts

openfoodfacts_api_useragent = os.getenv('openfoodfacts_api_useragent', 'openfoodfacts_api_useragent')
api = openfoodfacts.API(user_agent=openfoodfacts_api_useragent)

def trottleApiBy():
    """
    Returns a float value which is used to trottle api connections
    """
    print(type(flaskSession))
    # if flaskSession

    

def searchByStr(searchText):#Will Need to sanitize this
    try: 
        rtn = api.product.text_search(searchText)
        return rtn
    except:
        print("Exception in API Call")
        return -1

def searchByCode(code):
    try:
        rtn = api.product.get(code, fields=["code", "product_name"])
        return rtn
    except:
        print("Exception in API Call")
        return -1
code = "3017620422003"

# api.product.text_search("mineral water")
# {"count": 3006628, "page": 1, "page_count": 20, "page_size": 20, "products": [{...}], "skip": 0}

# test = searchByStr("mineral water")
# print(type)
# print(test)
trottleApiBy()
