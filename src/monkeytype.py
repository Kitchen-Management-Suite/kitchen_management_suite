"""
File: monkeytype.py
Path: src/monkeytype.py
Author: Rohan Plante, Thomas Bruce, Enhanced by Claude
Date-Created: 10/23/2025
Date-Modified: 11/03/2025

Description:
    Advanced database population script for the Kitchen Management Suite.
    Generates realistic users with organic household groupings.
    Creates realistic recipes with matching ingredients from a curated pantry item pool.
    Tests all database relationships including edge cases.

Usage:
    python monkeytype.py
    python monkeytype.py --users 100
"""

import argparse
import random
import datetime
import requests
from bs4 import BeautifulSoup
import tomli
import json

from faker import Faker
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

# Adjust these imports to match your actual project structure
from db.server import get_session, init_database
from db.schema import (
    User, UserProfile, UserNutrition, Role, Household, Member, 
    Pantry, Item, Recipe, Adds, Authors, Holds
)

fake = Faker()
random.seed(2381)  # Deterministic for testing

# Defaults
DEFAULT_USERS = 50

# Dietary preferences and allergies pools
DIETARY_PREFS = [
    "vegetarian", "vegan", "pescatarian", "keto", "paleo", 
    "gluten-free", "dairy-free", "low-carb", "mediterranean", None
]

ALLERGIES = [
    "peanuts", "tree nuts", "shellfish", "dairy", "eggs", 
    "soy", "wheat", "fish", None, None, None  # weighted toward no allergies
]

# Comprehensive realistic ingredient pool organized by category
# Each ingredient includes realistic nutritional data per 100g (matching Open Food Facts format)
INGREDIENT_POOL = {
    "proteins": {
        "chicken breast": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0, "sugar": 0, "sodium": 74},
        "ground beef": {"calories": 250, "protein": 26, "carbs": 0, "fat": 17, "fiber": 0, "sugar": 0, "sodium": 75},
        "pork chops": {"calories": 231, "protein": 25.7, "carbs": 0, "fat": 13.9, "fiber": 0, "sugar": 0, "sodium": 62},
        "salmon": {"calories": 208, "protein": 20, "carbs": 0, "fat": 13, "fiber": 0, "sugar": 0, "sodium": 59},
        "tuna": {"calories": 132, "protein": 28, "carbs": 0, "fat": 1.3, "fiber": 0, "sugar": 0, "sodium": 47},
        "shrimp": {"calories": 99, "protein": 24, "carbs": 0.2, "fat": 0.3, "fiber": 0, "sugar": 0, "sodium": 111},
        "eggs": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0, "sugar": 1.1, "sodium": 124},
        "tofu": {"calories": 76, "protein": 8, "carbs": 1.9, "fat": 4.8, "fiber": 0.3, "sugar": 0.7, "sodium": 7},
        "chickpeas": {"calories": 164, "protein": 8.9, "carbs": 27.4, "fat": 2.6, "fiber": 7.6, "sugar": 4.8, "sodium": 7},
        "black beans": {"calories": 132, "protein": 8.9, "carbs": 23.7, "fat": 0.5, "fiber": 8.7, "sugar": 0.3, "sodium": 2},
        "lentils": {"calories": 116, "protein": 9, "carbs": 20, "fat": 0.4, "fiber": 7.9, "sugar": 1.8, "sodium": 2},
        "ground turkey": {"calories": 203, "protein": 27.4, "carbs": 0, "fat": 9.8, "fiber": 0, "sugar": 0, "sodium": 70},
        "bacon": {"calories": 541, "protein": 37, "carbs": 1.4, "fat": 42, "fiber": 0, "sugar": 0, "sodium": 1717},
        "ham": {"calories": 145, "protein": 21, "carbs": 1.5, "fat": 5.5, "fiber": 0, "sugar": 0, "sodium": 1203},
        "turkey breast": {"calories": 135, "protein": 30, "carbs": 0, "fat": 0.7, "fiber": 0, "sugar": 0, "sodium": 55},
        "cod": {"calories": 82, "protein": 18, "carbs": 0, "fat": 0.7, "fiber": 0, "sugar": 0, "sodium": 54},
        "tilapia": {"calories": 96, "protein": 20, "carbs": 0, "fat": 1.7, "fiber": 0, "sugar": 0, "sodium": 52}
    },
    "dairy": {
        "milk": {"calories": 42, "protein": 3.4, "carbs": 5, "fat": 1, "fiber": 0, "sugar": 5, "sodium": 44},
        "butter": {"calories": 717, "protein": 0.9, "carbs": 0.1, "fat": 81, "fiber": 0, "sugar": 0.1, "sodium": 11},
        "cheddar cheese": {"calories": 403, "protein": 25, "carbs": 1.3, "fat": 33, "fiber": 0, "sugar": 0.5, "sodium": 621},
        "mozzarella cheese": {"calories": 280, "protein": 28, "carbs": 2.2, "fat": 17, "fiber": 0, "sugar": 1, "sodium": 373},
        "parmesan cheese": {"calories": 431, "protein": 38, "carbs": 4.1, "fat": 29, "fiber": 0, "sugar": 0.9, "sodium": 1529},
        "cream cheese": {"calories": 342, "protein": 5.9, "carbs": 5.5, "fat": 34, "fiber": 0, "sugar": 3.2, "sodium": 296},
        "sour cream": {"calories": 193, "protein": 2.4, "carbs": 4.6, "fat": 19, "fiber": 0, "sugar": 2.9, "sodium": 58},
        "heavy cream": {"calories": 340, "protein": 2.1, "carbs": 2.8, "fat": 36, "fiber": 0, "sugar": 2.8, "sodium": 38},
        "yogurt": {"calories": 59, "protein": 10, "carbs": 3.6, "fat": 0.4, "fiber": 0, "sugar": 3.2, "sodium": 36},
        "feta cheese": {"calories": 264, "protein": 14, "carbs": 4.1, "fat": 21, "fiber": 0, "sugar": 4.1, "sodium": 1116},
        "ricotta cheese": {"calories": 174, "protein": 11, "carbs": 3.0, "fat": 13, "fiber": 0, "sugar": 0.3, "sodium": 84},
        "goat cheese": {"calories": 364, "protein": 21, "carbs": 2.6, "fat": 30, "fiber": 0, "sugar": 2.6, "sodium": 515}
    },
    "vegetables": {
        "tomatoes": {"calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2, "fiber": 1.2, "sugar": 2.6, "sodium": 5},
        "onions": {"calories": 40, "protein": 1.1, "carbs": 9.3, "fat": 0.1, "fiber": 1.7, "sugar": 4.2, "sodium": 4},
        "garlic": {"calories": 149, "protein": 6.4, "carbs": 33, "fat": 0.5, "fiber": 2.1, "sugar": 1, "sodium": 17},
        "bell peppers": {"calories": 26, "protein": 0.9, "carbs": 6, "fat": 0.3, "fiber": 2.1, "sugar": 4.2, "sodium": 4},
        "carrots": {"calories": 41, "protein": 0.9, "carbs": 10, "fat": 0.2, "fiber": 2.8, "sugar": 4.7, "sodium": 69},
        "celery": {"calories": 14, "protein": 0.7, "carbs": 3, "fat": 0.2, "fiber": 1.6, "sugar": 1.3, "sodium": 80},
        "broccoli": {"calories": 34, "protein": 2.8, "carbs": 7, "fat": 0.4, "fiber": 2.6, "sugar": 1.7, "sodium": 33},
        "spinach": {"calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2, "sugar": 0.4, "sodium": 79},
        "lettuce": {"calories": 15, "protein": 1.4, "carbs": 2.9, "fat": 0.2, "fiber": 1.3, "sugar": 0.8, "sodium": 28},
        "cucumber": {"calories": 15, "protein": 0.7, "carbs": 3.6, "fat": 0.1, "fiber": 0.5, "sugar": 1.7, "sodium": 2},
        "zucchini": {"calories": 17, "protein": 1.2, "carbs": 3.1, "fat": 0.3, "fiber": 1, "sugar": 2.5, "sodium": 8},
        "mushrooms": {"calories": 22, "protein": 3.1, "carbs": 3.3, "fat": 0.3, "fiber": 1, "sugar": 2, "sodium": 5},
        "potatoes": {"calories": 77, "protein": 2, "carbs": 17, "fat": 0.1, "fiber": 2.1, "sugar": 0.8, "sodium": 6},
        "sweet potatoes": {"calories": 86, "protein": 1.6, "carbs": 20, "fat": 0.1, "fiber": 3, "sugar": 4.2, "sodium": 55},
        "green beans": {"calories": 31, "protein": 1.8, "carbs": 7, "fat": 0.2, "fiber": 2.7, "sugar": 3.3, "sodium": 6},
        "cauliflower": {"calories": 25, "protein": 1.9, "carbs": 5, "fat": 0.3, "fiber": 2, "sugar": 1.9, "sodium": 30},
        "asparagus": {"calories": 20, "protein": 2.2, "carbs": 3.9, "fat": 0.1, "fiber": 2.1, "sugar": 1.9, "sodium": 2},
        "corn": {"calories": 86, "protein": 3.3, "carbs": 19, "fat": 1.4, "fiber": 2, "sugar": 6.3, "sodium": 15},
        "peas": {"calories": 81, "protein": 5.4, "carbs": 14, "fat": 0.4, "fiber": 5.7, "sugar": 5.7, "sodium": 5},
        "kale": {"calories": 49, "protein": 4.3, "carbs": 9, "fat": 0.9, "fiber": 3.6, "sugar": 2.3, "sodium": 38},
        "cabbage": {"calories": 25, "protein": 1.3, "carbs": 5.8, "fat": 0.1, "fiber": 2.5, "sugar": 3.2, "sodium": 18},
        "eggplant": {"calories": 25, "protein": 1, "carbs": 5.9, "fat": 0.2, "fiber": 3, "sugar": 3.5, "sodium": 2},
        "jalapeños": {"calories": 29, "protein": 0.9, "carbs": 6.5, "fat": 0.4, "fiber": 2.8, "sugar": 4.1, "sodium": 3}
    },
    "fruits": {
        "apples": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2, "fiber": 2.4, "sugar": 10, "sodium": 1},
        "bananas": {"calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3, "fiber": 2.6, "sugar": 12, "sodium": 1},
        "oranges": {"calories": 47, "protein": 0.9, "carbs": 12, "fat": 0.1, "fiber": 2.4, "sugar": 9, "sodium": 0},
        "lemons": {"calories": 29, "protein": 1.1, "carbs": 9, "fat": 0.3, "fiber": 2.8, "sugar": 2.5, "sodium": 2},
        "limes": {"calories": 30, "protein": 0.7, "carbs": 11, "fat": 0.2, "fiber": 2.8, "sugar": 1.7, "sodium": 2},
        "strawberries": {"calories": 32, "protein": 0.7, "carbs": 7.7, "fat": 0.3, "fiber": 2, "sugar": 4.9, "sodium": 1},
        "blueberries": {"calories": 57, "protein": 0.7, "carbs": 14, "fat": 0.3, "fiber": 2.4, "sugar": 10, "sodium": 1},
        "raspberries": {"calories": 52, "protein": 1.2, "carbs": 12, "fat": 0.7, "fiber": 6.5, "sugar": 4.4, "sodium": 1},
        "grapes": {"calories": 69, "protein": 0.7, "carbs": 18, "fat": 0.2, "fiber": 0.9, "sugar": 15, "sodium": 2},
        "avocados": {"calories": 160, "protein": 2, "carbs": 8.5, "fat": 15, "fiber": 6.7, "sugar": 0.7, "sodium": 7},
        "mangoes": {"calories": 60, "protein": 0.8, "carbs": 15, "fat": 0.4, "fiber": 1.6, "sugar": 14, "sodium": 1},
        "pineapple": {"calories": 50, "protein": 0.5, "carbs": 13, "fat": 0.1, "fiber": 1.4, "sugar": 10, "sodium": 1},
        "watermelon": {"calories": 30, "protein": 0.6, "carbs": 7.6, "fat": 0.2, "fiber": 0.4, "sugar": 6.2, "sodium": 1},
        "peaches": {"calories": 39, "protein": 0.9, "carbs": 10, "fat": 0.3, "fiber": 1.5, "sugar": 8.4, "sodium": 0},
        "pears": {"calories": 57, "protein": 0.4, "carbs": 15, "fat": 0.1, "fiber": 3.1, "sugar": 10, "sodium": 1}
    },
    "grains": {
        "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4, "sugar": 0.1, "sodium": 1},
        "pasta": {"calories": 131, "protein": 5, "carbs": 25, "fat": 1.1, "fiber": 1.8, "sugar": 0.6, "sodium": 6},
        "bread": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2, "fiber": 2.7, "sugar": 5, "sodium": 491},
        "flour": {"calories": 364, "protein": 10, "carbs": 76, "fat": 1, "fiber": 2.7, "sugar": 0.3, "sodium": 2},
        "oats": {"calories": 389, "protein": 17, "carbs": 66, "fat": 6.9, "fiber": 11, "sugar": 0.8, "sodium": 2},
        "quinoa": {"calories": 120, "protein": 4.4, "carbs": 21, "fat": 1.9, "fiber": 2.8, "sugar": 0.9, "sodium": 7},
        "couscous": {"calories": 112, "protein": 3.8, "carbs": 23, "fat": 0.2, "fiber": 1.4, "sugar": 0.1, "sodium": 5},
        "tortillas": {"calories": 218, "protein": 6, "carbs": 36, "fat": 6, "fiber": 2.3, "sugar": 1.9, "sodium": 389},
        "bagels": {"calories": 257, "protein": 10, "carbs": 50, "fat": 1.7, "fiber": 2.3, "sugar": 6.6, "sodium": 430},
        "crackers": {"calories": 502, "protein": 8.2, "carbs": 62, "fat": 24, "fiber": 2.5, "sugar": 1.4, "sodium": 698},
        "breadcrumbs": {"calories": 395, "protein": 13, "carbs": 72, "fat": 5.3, "fiber": 4.5, "sugar": 6.2, "sodium": 732},
        "pizza dough": {"calories": 233, "protein": 7.7, "carbs": 44, "fat": 2.7, "fiber": 2.1, "sugar": 1.9, "sodium": 417}
    },
    "pantry_staples": {
        "olive oil": {"calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0, "sugar": 0, "sodium": 2},
        "vegetable oil": {"calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0, "sugar": 0, "sodium": 0},
        "canola oil": {"calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0, "sugar": 0, "sodium": 0},
        "salt": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 38758},
        "black pepper": {"calories": 251, "protein": 10, "carbs": 64, "fat": 3.3, "fiber": 25, "sugar": 0.6, "sodium": 20},
        "sugar": {"calories": 387, "protein": 0, "carbs": 100, "fat": 0, "fiber": 0, "sugar": 100, "sodium": 1},
        "brown sugar": {"calories": 380, "protein": 0, "carbs": 98, "fat": 0, "fiber": 0, "sugar": 97, "sodium": 39},
        "honey": {"calories": 304, "protein": 0.3, "carbs": 82, "fat": 0, "fiber": 0.2, "sugar": 82, "sodium": 4},
        "soy sauce": {"calories": 53, "protein": 8, "carbs": 4.9, "fat": 0.1, "fiber": 0.8, "sugar": 0.4, "sodium": 5586},
        "balsamic vinegar": {"calories": 88, "protein": 0.5, "carbs": 17, "fat": 0, "fiber": 0, "sugar": 14, "sodium": 23},
        "white vinegar": {"calories": 18, "protein": 0, "carbs": 0.04, "fat": 0, "fiber": 0, "sugar": 0.04, "sodium": 2},
        "apple cider vinegar": {"calories": 21, "protein": 0, "carbs": 0.9, "fat": 0, "fiber": 0, "sugar": 0.4, "sodium": 5},
        "ketchup": {"calories": 101, "protein": 1.2, "carbs": 25, "fat": 0.1, "fiber": 0.3, "sugar": 21, "sodium": 1042},
        "mustard": {"calories": 60, "protein": 3.7, "carbs": 5.3, "fat": 3.3, "fiber": 3, "sugar": 2.8, "sodium": 1135},
        "mayonnaise": {"calories": 680, "protein": 0.9, "carbs": 0.6, "fat": 75, "fiber": 0, "sugar": 0.3, "sodium": 544},
        "hot sauce": {"calories": 12, "protein": 0.6, "carbs": 2.8, "fat": 0.2, "fiber": 0.5, "sugar": 0.8, "sodium": 1145},
        "worcestershire sauce": {"calories": 78, "protein": 0, "carbs": 19, "fat": 0, "fiber": 0, "sugar": 16, "sodium": 1361},
        "chicken broth": {"calories": 4, "protein": 0.4, "carbs": 0.3, "fat": 0.2, "fiber": 0, "sugar": 0.3, "sodium": 343},
        "beef broth": {"calories": 4, "protein": 0.5, "carbs": 0.4, "fat": 0.2, "fiber": 0, "sugar": 0.4, "sodium": 343},
        "vegetable broth": {"calories": 4, "protein": 0.2, "carbs": 0.9, "fat": 0, "fiber": 0, "sugar": 0.4, "sodium": 343},
        "tomato paste": {"calories": 82, "protein": 4.3, "carbs": 19, "fat": 0.5, "fiber": 4.1, "sugar": 12, "sodium": 59},
        "tomato sauce": {"calories": 24, "protein": 1.2, "carbs": 5.3, "fat": 0.1, "fiber": 1.5, "sugar": 3.5, "sodium": 321},
        "canned tomatoes": {"calories": 32, "protein": 1.6, "carbs": 7.3, "fat": 0.2, "fiber": 1.9, "sugar": 4.7, "sodium": 130},
        "peanut butter": {"calories": 588, "protein": 25, "carbs": 20, "fat": 50, "fiber": 6, "sugar": 9, "sodium": 429},
        "jam": {"calories": 278, "protein": 0.4, "carbs": 69, "fat": 0.1, "fiber": 1.1, "sugar": 49, "sodium": 32},
        "maple syrup": {"calories": 260, "protein": 0, "carbs": 67, "fat": 0.1, "fiber": 0, "sugar": 60, "sodium": 12}
    },
    "spices": {
        "basil": {"calories": 23, "protein": 3.2, "carbs": 2.7, "fat": 0.6, "fiber": 1.6, "sugar": 0.3, "sodium": 4},
        "oregano": {"calories": 265, "protein": 9, "carbs": 69, "fat": 4.3, "fiber": 42, "sugar": 4, "sodium": 25},
        "thyme": {"calories": 101, "protein": 5.6, "carbs": 24, "fat": 1.7, "fiber": 14, "sugar": 0, "sodium": 9},
        "rosemary": {"calories": 131, "protein": 3.3, "carbs": 20, "fat": 5.9, "fiber": 15, "sugar": 0, "sodium": 26},
        "parsley": {"calories": 36, "protein": 3, "carbs": 6.3, "fat": 0.8, "fiber": 3.3, "sugar": 0.9, "sodium": 56},
        "cilantro": {"calories": 23, "protein": 2.1, "carbs": 3.7, "fat": 0.5, "fiber": 2.8, "sugar": 0.9, "sodium": 46},
        "cumin": {"calories": 375, "protein": 18, "carbs": 44, "fat": 22, "fiber": 11, "sugar": 2.2, "sodium": 168},
        "paprika": {"calories": 282, "protein": 14, "carbs": 54, "fat": 13, "fiber": 35, "sugar": 10, "sodium": 68},
        "chili powder": {"calories": 282, "protein": 13, "carbs": 50, "fat": 14, "fiber": 35, "sugar": 7.2, "sodium": 1640},
        "garlic powder": {"calories": 331, "protein": 17, "carbs": 73, "fat": 0.7, "fiber": 9, "sugar": 2.4, "sodium": 27},
        "onion powder": {"calories": 341, "protein": 10, "carbs": 79, "fat": 1.0, "fiber": 15, "sugar": 7.5, "sodium": 77},
        "cinnamon": {"calories": 247, "protein": 4, "carbs": 81, "fat": 1.2, "fiber": 53, "sugar": 2.2, "sodium": 10},
        "nutmeg": {"calories": 525, "protein": 5.8, "carbs": 49, "fat": 36, "fiber": 21, "sugar": 28, "sodium": 16},
        "ginger": {"calories": 80, "protein": 1.8, "carbs": 18, "fat": 0.8, "fiber": 2, "sugar": 1.7, "sodium": 13},
        "turmeric": {"calories": 312, "protein": 10, "carbs": 67, "fat": 3.2, "fiber": 23, "sugar": 3.2, "sodium": 27},
        "curry powder": {"calories": 325, "protein": 14, "carbs": 56, "fat": 14, "fiber": 53, "sugar": 3, "sodium": 52},
        "red pepper flakes": {"calories": 318, "protein": 12, "carbs": 57, "fat": 17, "fiber": 28, "sugar": 10, "sodium": 91},
        "italian seasoning": {"calories": 285, "protein": 10, "carbs": 64, "fat": 4, "fiber": 38, "sugar": 6, "sodium": 35},
        "bay leaves": {"calories": 313, "protein": 7.6, "carbs": 75, "fat": 8.4, "fiber": 26, "sugar": 0, "sodium": 23}
    },
    "nuts_seeds": {
        "almonds": {"calories": 579, "protein": 21, "carbs": 22, "fat": 50, "fiber": 12, "sugar": 4.4, "sodium": 1},
        "walnuts": {"calories": 654, "protein": 15, "carbs": 14, "fat": 65, "fiber": 6.7, "sugar": 2.6, "sodium": 2},
        "pecans": {"calories": 691, "protein": 9, "carbs": 14, "fat": 72, "fiber": 9.6, "sugar": 4, "sodium": 0},
        "cashews": {"calories": 553, "protein": 18, "carbs": 30, "fat": 44, "fiber": 3.3, "sugar": 6, "sodium": 12},
        "peanuts": {"calories": 567, "protein": 26, "carbs": 16, "fat": 49, "fiber": 8.5, "sugar": 4.7, "sodium": 18},
        "sunflower seeds": {"calories": 584, "protein": 21, "carbs": 20, "fat": 51, "fiber": 8.6, "sugar": 2.6, "sodium": 9},
        "chia seeds": {"calories": 486, "protein": 17, "carbs": 42, "fat": 31, "fiber": 34, "sugar": 0, "sodium": 16},
        "flax seeds": {"calories": 534, "protein": 18, "carbs": 29, "fat": 42, "fiber": 27, "sugar": 1.6, "sodium": 30},
        "sesame seeds": {"calories": 573, "protein": 18, "carbs": 23, "fat": 50, "fiber": 12, "sugar": 0.3, "sodium": 11},
        "pine nuts": {"calories": 673, "protein": 14, "carbs": 13, "fat": 68, "fiber": 3.7, "sugar": 3.6, "sodium": 2}
    },
    "baking": {
        "baking powder": {"calories": 53, "protein": 0, "carbs": 28, "fat": 0, "fiber": 0.2, "sugar": 0, "sodium": 10600},
        "baking soda": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 27360},
        "vanilla extract": {"calories": 288, "protein": 0.1, "carbs": 13, "fat": 0.1, "fiber": 0, "sugar": 13, "sodium": 9},
        "chocolate chips": {"calories": 479, "protein": 4.2, "carbs": 63, "fat": 24, "fiber": 7, "sugar": 52, "sodium": 24},
        "cocoa powder": {"calories": 228, "protein": 20, "carbs": 58, "fat": 14, "fiber": 33, "sugar": 1.8, "sodium": 21},
        "cornstarch": {"calories": 381, "protein": 0.3, "carbs": 91, "fat": 0.1, "fiber": 0.9, "sugar": 0, "sodium": 9},
        "yeast": {"calories": 325, "protein": 41, "carbs": 41, "fat": 7.6, "fiber": 27, "sugar": 0, "sodium": 51}
    }
}

# Cuisine-specific ingredient preferences (using ingredient keys)
CUISINE_INGREDIENTS = {
    "Italian": ["pasta", "tomatoes", "basil", "oregano", "parmesan cheese", "olive oil", "garlic", "mozzarella cheese"],
    "Mexican": ["tortillas", "black beans", "jalapeños", "cilantro", "limes", "cumin", "chili powder", "avocados"],
    "Chinese": ["rice", "soy sauce", "ginger", "garlic", "vegetable oil", "green beans", "chicken breast"],
    "Indian": ["curry powder", "turmeric", "cumin", "ginger", "garlic", "chickpeas", "lentils", "rice"],
    "American": ["ground beef", "potatoes", "cheddar cheese", "bacon", "butter", "milk", "bread"],
    "Mediterranean": ["olive oil", "feta cheese", "tomatoes", "cucumber", "lemons", "garlic", "chickpeas"],
    "Japanese": ["rice", "soy sauce", "ginger", "sesame seeds", "tofu"],
    "French": ["butter", "heavy cream", "garlic", "parsley", "cheddar cheese"],
    "Thai": ["rice", "limes", "cilantro", "chili powder", "ginger"]
}

# Recipe templates with realistic structure
RECIPE_COURSES = ["appetizer", "main course", "side dish", "dessert", "breakfast", "snack", "beverage"]

class DataFetcher:
    """Fetches real data from external APIs"""
    
    BASE_TREE_URL = "https://git.sr.ht/~martijnbraam/fathub-data/tree/master/item/en/recipes"
    BASE_BLOB_URL = "https://git.sr.ht/~martijnbraam/fathub-data/blob/master/en/recipes/"

    @staticmethod
    def fetch_fathub_recipes(limit=30):
        """Fetch recipes recursively from Fathub TOML blobs"""
        recipes = []
        visited_folders = set()

        def fetch_tree(url, subpath=""):
            """Recursively crawl folders to get all TOML blobs"""
            if subpath in visited_folders or len(recipes) >= limit:
                return recipes
            visited_folders.add(subpath)

            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # Folders
                for div in soup.select("div.name.tree > a"):
                    if len(recipes) >= limit:
                        return recipes
                    folder_name = div.text.strip()
                    href = div.get("href")
                    if folder_name == ".." or not href:
                        continue
                    new_subpath = f"{subpath}{folder_name}/"
                    tree_url = "https://git.sr.ht" + href
                    fetch_tree(tree_url, new_subpath)

                # Files (TOML blobs)
                for div in soup.select("div.name.blob > a"):
                    if len(recipes) >= limit:
                        return recipes
                    file_name = div.text.strip()
                    if not file_name.endswith(".toml"):
                        continue

                    blob_url = DataFetcher.BASE_BLOB_URL + subpath + file_name
                    try:
                        blob_resp = requests.get(blob_url, timeout=10)
                        blob_resp.raise_for_status()
                        toml_data = tomli.loads(blob_resp.text)

                        # Flatten instructions
                        instructions = []
                        for block in toml_data.get("instructions", []):
                            instructions.extend(block.get("steps", []))

                        recipe_dict = {
                            "name": toml_data.get("name", "Unnamed Recipe"),
                            "author": toml_data.get("author", None),
                            "created": str(toml_data.get("created", "")),
                            "cuisine": toml_data.get("cuisine", ""),
                            "course": toml_data.get("course", ""),
                            "preptime": toml_data.get("preptime", 0),
                            "cooktime": toml_data.get("cooktime", 0),
                            "serves": toml_data.get("serves", 1),
                            "ingredients": {k: dict(v) for k, v in toml_data.get("ingredients", {}).items()},
                            "instructions": instructions,
                        }
                        recipes.append(recipe_dict)

                    except Exception as e:
                        print(f"⚠️ Failed to fetch/parse recipe {blob_url}: {e}")

            except Exception as e:
                print(f"⚠️ Failed to fetch tree {url}: {e}")

            return recipes

        return fetch_tree(DataFetcher.BASE_TREE_URL)


class RealisticItemGenerator:
    """Generates realistic pantry items with Open Food Facts-style nutrition data"""
    
    @staticmethod
    def generate_items():
        """Create all items from the ingredient pool with nutrition data"""
        items = []
        
        # Create items from each category with nutrition information
        for category, ingredients_dict in INGREDIENT_POOL.items():
            for ingredient_name, nutrition in ingredients_dict.items():
                # Create Open Food Facts-style data structure
                item_data = {
                    'name': ingredient_name.title(),
                    'category': category,
                    'source': 'custom',
                    'common': True,
                    # Nutriments matching Open Food Facts structure
                    'nutriments': {
                        'energy-kcal_100g': nutrition['calories'],
                        'energy-kcal': nutrition['calories'],
                        'energy_100g': nutrition['calories'] * 4.184,  # Convert to kJ
                        'energy': nutrition['calories'] * 4.184,
                        'proteins_100g': nutrition['protein'],
                        'proteins': nutrition['protein'],
                        'carbohydrates_100g': nutrition['carbs'],
                        'carbohydrates': nutrition['carbs'],
                        'fat_100g': nutrition['fat'],
                        'fat': nutrition['fat'],
                        'fiber_100g': nutrition['fiber'],
                        'fiber': nutrition['fiber'],
                        'sugars_100g': nutrition['sugar'],
                        'sugars': nutrition['sugar'],
                        'sodium_100g': nutrition['sodium'] / 1000,  # Convert mg to g
                        'sodium': nutrition['sodium'] / 1000,
                        'salt_100g': (nutrition['sodium'] / 1000) * 2.5,  # Convert sodium to salt
                        'salt': (nutrition['sodium'] / 1000) * 2.5,
                    },
                    # Additional metadata
                    'serving_size': '100g',
                    'nutrition_grade': RealisticItemGenerator._calculate_nutriscore(nutrition),
                    'nova_group': RealisticItemGenerator._estimate_nova_group(category, ingredient_name),
                    'allergens': RealisticItemGenerator._get_allergens(ingredient_name, category),
                }
                items.append(item_data)
        
        print(f"✓ Generated {len(items)} realistic items with nutrition data")
        return items
    
    @staticmethod
    def _calculate_nutriscore(nutrition):
        """Calculate a simple Nutri-Score (A-E) based on nutrition values"""
        # Simplified Nutri-Score calculation
        points = 0
        
        # Negative points (bad nutrients)
        energy = nutrition['calories']
        if energy > 335: points += 10
        elif energy > 270: points += 8
        elif energy > 210: points += 6
        elif energy > 150: points += 4
        elif energy > 80: points += 2
        
        sugars = nutrition['sugar']
        if sugars > 45: points += 10
        elif sugars > 36: points += 9
        elif sugars > 27: points += 8
        elif sugars > 22.5: points += 7
        elif sugars > 18: points += 6
        elif sugars > 13.5: points += 5
        elif sugars > 9: points += 4
        elif sugars > 4.5: points += 3
        
        sodium = nutrition['sodium']
        if sodium > 900: points += 10
        elif sodium > 810: points += 9
        elif sodium > 720: points += 8
        elif sodium > 630: points += 7
        elif sodium > 540: points += 6
        elif sodium > 450: points += 5
        elif sodium > 360: points += 4
        elif sodium > 270: points += 3
        elif sodium > 90: points += 1
        
        # Positive points (good nutrients)
        fiber = nutrition['fiber']
        if fiber > 4.7: points -= 5
        elif fiber > 3.7: points -= 4
        elif fiber > 2.8: points -= 3
        elif fiber > 1.9: points -= 2
        elif fiber > 0.9: points -= 1
        
        protein = nutrition['protein']
        if protein > 8: points -= 5
        elif protein > 6.4: points -= 4
        elif protein > 4.8: points -= 3
        elif protein > 3.2: points -= 2
        elif protein > 1.6: points -= 1
        
        # Convert points to grade
        if points < -1: return 'a'
        elif points <= 2: return 'b'
        elif points <= 10: return 'c'
        elif points <= 18: return 'd'
        else: return 'e'
    
    @staticmethod
    def _estimate_nova_group(category, ingredient_name):
        """Estimate NOVA group (1-4) based on processing level"""
        # NOVA Group 1: Unprocessed or minimally processed foods
        if category in ["vegetables", "fruits", "nuts_seeds"] and "oil" not in ingredient_name:
            return 1
        
        # NOVA Group 2: Processed culinary ingredients
        if category in ["pantry_staples", "spices", "baking"]:
            if ingredient_name in ["olive oil", "vegetable oil", "canola oil", "butter", "salt", "sugar", "honey"]:
                return 2
        
        # NOVA Group 3: Processed foods
        if category in ["dairy", "proteins", "grains"]:
            if ingredient_name in ["cheese", "bread", "bacon", "ham", "canned tomatoes"]:
                return 3
        
        # NOVA Group 4: Ultra-processed foods
        if ingredient_name in ["ketchup", "mayonnaise", "hot sauce", "crackers", "chocolate chips"]:
            return 4
        
        # Default to Group 2
        return 2
    
    @staticmethod
    def _get_allergens(ingredient_name, category):
        """Return common allergens present in the ingredient"""
        allergens = []
        
        # Dairy allergens
        if category == "dairy" or "cheese" in ingredient_name or "milk" in ingredient_name or "butter" in ingredient_name or "cream" in ingredient_name or "yogurt" in ingredient_name:
            allergens.append("milk")
        
        # Egg allergens
        if "eggs" in ingredient_name:
            allergens.append("eggs")
        
        # Nut allergens
        if category == "nuts_seeds":
            if "peanut" in ingredient_name:
                allergens.append("peanuts")
            elif ingredient_name in ["almonds", "walnuts", "pecans", "cashews", "pine nuts"]:
                allergens.append("tree-nuts")
        
        # Gluten allergens
        if category == "grains" and ingredient_name in ["bread", "pasta", "flour", "bagels", "crackers", "breadcrumbs", "pizza dough"]:
            allergens.append("gluten")
        
        # Soy allergens
        if "soy" in ingredient_name or "tofu" in ingredient_name:
            allergens.append("soybeans")
        
        # Shellfish
        if ingredient_name == "shrimp":
            allergens.append("crustaceans")
        
        # Fish
        if ingredient_name in ["salmon", "tuna", "cod", "tilapia"]:
            allergens.append("fish")
        
        return allergens


class RealisticRecipeGenerator:
    """Generates realistic recipes using items from the ingredient pool"""
    
    # Recipe name templates for different cuisines
    RECIPE_TEMPLATES = {
        "Italian": [
            "{protein} Pasta", "Baked {protein}", "{vegetable} Risotto",
            "Creamy {vegetable} Pasta", "{protein} Parmesan"
        ],
        "Mexican": [
            "{protein} Tacos", "{protein} Burrito Bowl", "{vegetable} Quesadilla",
            "{protein} Enchiladas", "Spicy {protein} Skillet"
        ],
        "Chinese": [
            "{protein} Stir Fry", "Sweet and Sour {protein}", "{protein} Fried Rice",
            "{vegetable} Lo Mein", "Garlic {protein}"
        ],
        "Indian": [
            "{protein} Curry", "{vegetable} Masala", "{protein} Tikka",
            "Spiced {vegetable} Stew", "{protein} Biryani"
        ],
        "American": [
            "Classic {protein} Sandwich", "Grilled {protein}", "{protein} Burger",
            "Roasted {protein}", "{protein} Casserole"
        ],
        "Mediterranean": [
            "{protein} Bowl", "Mediterranean {vegetable} Salad", "{protein} Wrap",
            "Lemon Herb {protein}", "{vegetable} Platter"
        ],
        "Japanese": [
            "{protein} Teriyaki", "{protein} Bowl", "{vegetable} Sushi Roll",
            "Miso {protein}", "{protein} Ramen"
        ],
        "French": [
            "{protein} au Vin", "French {vegetable} Gratin", "Herb {protein}",
            "Provence {protein}", "Butter {protein}"
        ]
    }
    
    @staticmethod
    def get_all_ingredients_flat():
        """Get a flat list of all ingredient names"""
        all_ingredients = []
        for category, ingredients_dict in INGREDIENT_POOL.items():
            all_ingredients.extend(ingredients_dict.keys())
        return all_ingredients
    
    @staticmethod
    def generate_recipe_name(cuisine):
        """Generate a realistic recipe name based on cuisine"""
        templates = RealisticRecipeGenerator.RECIPE_TEMPLATES.get(
            cuisine, 
            ["{protein} with {vegetable}", "Homemade {protein}", "Simple {vegetable} Dish"]
        )
        template = random.choice(templates)
        
        # Select appropriate ingredients
        protein = random.choice(list(INGREDIENT_POOL["proteins"].keys())).title()
        vegetable = random.choice(list(INGREDIENT_POOL["vegetables"].keys())).title()
        
        # Fill template
        name = template.format(protein=protein, vegetable=vegetable)
        return name
    
    @staticmethod
    def _get_ingredient_from_any_category(ingredient_name):
        """Find ingredient nutrition data from any category"""
        for category, ingredients_dict in INGREDIENT_POOL.items():
            if ingredient_name in ingredients_dict:
                return ingredients_dict[ingredient_name]
        return None
    
    @staticmethod
    def _calculate_recipe_nutrition(ingredients_dict, serves):
        """Calculate total nutrition for recipe based on ingredients (Fathub format)"""
        total_nutrition = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0,
            'sugar': 0,
            'sodium': 0
        }
        
        for ingredient_key, ingredient_info in ingredients_dict.items():
            # The ingredient ID is the clean identifier
            ingredient_id = ingredient_info.get('id', ingredient_key)
            # Convert back to searchable name (e.g., "olive-oil" -> "olive oil")
            ingredient_name = ingredient_id.replace("-", " ")
            amount = ingredient_info.get('amount', 1)
            
            # Find nutrition data
            nutrition = RealisticRecipeGenerator._get_ingredient_from_any_category(ingredient_name)
            if nutrition:
                # Assuming amount is in standard units (approximating to 100g equivalent)
                factor = amount * 0.5  # Rough conversion factor
                
                total_nutrition['calories'] += nutrition['calories'] * factor
                total_nutrition['protein'] += nutrition['protein'] * factor
                total_nutrition['carbs'] += nutrition['carbs'] * factor
                total_nutrition['fat'] += nutrition['fat'] * factor
                total_nutrition['fiber'] += nutrition['fiber'] * factor
                total_nutrition['sugar'] += nutrition['sugar'] * factor
                total_nutrition['sodium'] += nutrition['sodium'] * factor
        
        # Calculate per serving
        per_serving = {k: round(v / serves, 1) for k, v in total_nutrition.items()}
        
        return {
            'total': total_nutrition,
            'per_serving': per_serving
        }
    
    @staticmethod
    def generate_realistic_recipe(user_name=None):
        """Generate a single realistic recipe with nutrition data in Fathub format"""
        cuisine = random.choice(list(CUISINE_INGREDIENTS.keys()))
        course = random.choice(RECIPE_COURSES)
        serves = random.randint(2, 6)
        
        # Generate name
        recipe_name = RealisticRecipeGenerator.generate_recipe_name(cuisine)
        
        # Get cuisine-specific ingredients as base
        base_ingredients = CUISINE_INGREDIENTS.get(cuisine, [])
        
        # Add random ingredients from appropriate categories
        num_ingredients = random.randint(5, 12)
        selected_ingredients = []
        
        # Always include some base ingredients
        selected_ingredients.extend(random.sample(base_ingredients, min(3, len(base_ingredients))))
        
        # Add proteins
        if course in ["main course", "breakfast"]:
            selected_ingredients.append(random.choice(list(INGREDIENT_POOL["proteins"].keys())))
        
        # Add vegetables
        num_veggies = random.randint(2, 4)
        selected_ingredients.extend(random.sample(list(INGREDIENT_POOL["vegetables"].keys()), num_veggies))
        
        # Add pantry staples (always needed)
        selected_ingredients.extend(random.sample(list(INGREDIENT_POOL["pantry_staples"].keys()), random.randint(2, 4)))
        
        # Add spices
        selected_ingredients.extend(random.sample(list(INGREDIENT_POOL["spices"].keys()), random.randint(2, 4)))
        
        # Remove duplicates and limit to desired count
        selected_ingredients = list(set(selected_ingredients))[:num_ingredients]
        
        # Create ingredient dictionary with keys as ingredient names (Fathub format)
        ingredients = {}
        for ingredient in selected_ingredients:
            # Use a clean key (no spaces, lowercase)
            key = ingredient.lower().replace(" ", "")
            ingredients[key] = {
                "id": ingredient.lower().replace(" ", "-"),
                "amount": round(random.uniform(0.5, 4.0), 2),
                "unit": random.choice(["cup", "tablespoon", "teaspoon", "ounce", "pound", "piece", "clove", "to taste"])
            }
        
        # Calculate nutrition
        nutrition_data = RealisticRecipeGenerator._calculate_recipe_nutrition(ingredients, serves)
        
        # Generate instructions with ingredient references
        ingredient_keys = list(ingredients.keys())
        num_steps = random.randint(4, 8)
        instruction_templates = [
            f"Preheat oven to {random.choice([325, 350, 375, 400])}°F.",
            f"Season the [{random.choice(ingredient_keys)}] with salt and pepper.",
            f"Heat [{random.choice([k for k in ingredient_keys if 'oil' in k or 'butter' in k] or ingredient_keys)}] in a large pan over medium heat.",
            f"Add [{random.choice(ingredient_keys)}] and cook for {random.randint(3, 10)} minutes.",
            f"Stir in [{random.choice(ingredient_keys)}] and simmer.",
            f"Combine [{','.join(random.sample(ingredient_keys, min(3, len(ingredient_keys))))}] in a bowl and mix well.",
            f"Bake for {random.randint(20, 45)} minutes until golden brown.",
            f"Garnish with fresh [{random.choice([k for k in ingredient_keys if any(s in k for s in ['basil', 'parsley', 'cilantro'])] or ingredient_keys)}] and serve.",
            f"Let rest for {random.randint(5, 15)} minutes before serving.",
            f"Serve hot with [{random.choice([k for k in ingredient_keys if any(s in k for s in ['rice', 'pasta', 'bread'])] or ingredient_keys)}] on the side."
        ]
        instructions = random.sample(instruction_templates, min(num_steps, len(instruction_templates)))
        
        recipe_data = {
            "name": recipe_name,
            "author": user_name or fake.name(),
            "created": str(datetime.date.today() - datetime.timedelta(days=random.randint(0, 365))),
            "cuisine": cuisine,
            "course": course,
            "preptime": random.randint(10, 30),
            "cooktime": random.randint(15, 60),
            "serves": serves,
            "ingredients": ingredients,  # Now in proper Fathub format
            "instructions": instructions,
            # Add nutrition data matching Open Food Facts style
            "nutriments_per_serving": {
                "energy-kcal": nutrition_data['per_serving']['calories'],
                "energy": nutrition_data['per_serving']['calories'] * 4.184,
                "proteins": nutrition_data['per_serving']['protein'],
                "carbohydrates": nutrition_data['per_serving']['carbs'],
                "fat": nutrition_data['per_serving']['fat'],
                "fiber": nutrition_data['per_serving']['fiber'],
                "sugars": nutrition_data['per_serving']['sugar'],
                "sodium": nutrition_data['per_serving']['sodium'] / 1000,  # Convert to grams
                "salt": (nutrition_data['per_serving']['sodium'] / 1000) * 2.5
            },
            "nutriments_total": {
                "energy-kcal": nutrition_data['total']['calories'],
                "proteins": nutrition_data['total']['protein'],
                "carbohydrates": nutrition_data['total']['carbs'],
                "fat": nutrition_data['total']['fat'],
                "fiber": nutrition_data['total']['fiber'],
                "sugars": nutrition_data['total']['sugar'],
                "sodium": nutrition_data['total']['sodium'] / 1000
            }
        }
        
        return recipe_data


class UserGenerator:
    """Generates realistic users with profiles"""
    
    @staticmethod
    def create_user(first_name=None, last_name=None, age_range=(18, 70)):
        """Create a single user with realistic data"""
        first = first_name or fake.first_name()
        last = last_name or fake.last_name()
        
        # Realistic email patterns
        email_patterns = [
            f"{first.lower()}.{last.lower()}@{fake.free_email_domain()}",
            f"{first.lower()}{last.lower()}@{fake.free_email_domain()}",
            f"{first[0].lower()}{last.lower()}@{fake.free_email_domain()}",
            f"{first.lower()}{random.randint(1, 99)}@{fake.free_email_domain()}",
        ]
        email = random.choice(email_patterns)
        
        # Realistic username patterns
        username = f"{first.lower()}{last.lower()}{random.randint(1, 999)}"
        
        dob = fake.date_of_birth(minimum_age=age_range[0], maximum_age=age_range[1])
        
        user = User(
            FirstName=first,
            LastName=last,
            Username=username,
            Email=email,
            DateOfBirth=dob,
            Password=generate_password_hash("password123")
        )
        
        return user
    
    @staticmethod
    def create_profile(user):
        """Create user profile with realistic health data"""
        age = (datetime.date.today() - user.DateOfBirth).days // 365
        
        # Realistic height/weight based on age
        if age < 25:
            height = random.randint(160, 190)  # cm
            weight = random.randint(55, 90)    # kg
        else:
            height = random.randint(155, 185)
            weight = random.randint(60, 100)
        
        # Calorie goal based on age/weight
        base_calories = 1800 + (weight * 10) + random.randint(-200, 200)
        
        dietary_pref = random.choice(DIETARY_PREFS)
        allergy = random.choice(ALLERGIES)
        
        profile = UserProfile(
            UserID=user.UserID,
            Height=height,
            Weight=weight,
            CalorieGoal=base_calories,
            DietaryPreferences=dietary_pref,
            Allergies=allergy
        )
        
        return profile
    
    @staticmethod
    def create_nutrition_logs(user, days=30):
        """Create realistic nutrition logs for a user"""
        logs = []
        today = datetime.date.today()
        
        for day_offset in range(days):
            date = today - datetime.timedelta(days=day_offset)
            
            # 2-4 meals per day
            num_meals = random.randint(2, 4)
            meal_times = random.sample([
                datetime.time(7, 30),
                datetime.time(12, 0),
                datetime.time(18, 30),
                datetime.time(21, 0)
            ], num_meals)
            
            for meal_time in meal_times:
                calories = random.randint(300, 800)
                protein = random.uniform(10, 40)
                carbs = random.uniform(20, 80)
                fat = random.uniform(5, 35)
                
                log = UserNutrition(
                    UserID=user.UserID,
                    Date=date,
                    Time=meal_time,
                    CaloriesConsumed=calories,
                    Protein=protein,
                    Carbs=carbs,
                    Fat=fat,
                    Fiber=random.uniform(2, 10),
                    Sugar=random.uniform(5, 25),
                    Sodium=random.uniform(200, 1000)
                )
                logs.append(log)
        
        return logs


class HouseholdOrganizer:
    """Organically creates households from a pool of users"""
    
    @staticmethod
    def create_households_from_users(session, users):
        """
        Create realistic household groupings from users.
        Distributes users across families, roommate groups, and solo households.
        """
        households = []
        remaining_users = users.copy()
        random.shuffle(remaining_users)
        
        owner_role = session.query(Role).filter_by(RoleName="Owner").first()
        member_role = session.query(Role).filter_by(RoleName="Member").first()
        
        while remaining_users:
            # Decide household type based on remaining users
            if len(remaining_users) >= 4 and random.random() < 0.4:
                # Family household (2-5 members)
                size = min(random.randint(2, 5), len(remaining_users))
                members = remaining_users[:size]
                remaining_users = remaining_users[size:]
                
                # Use last name of first member
                household_name = f"{members[0].LastName} Family"
                household_type = "family"
                
            elif len(remaining_users) >= 3 and random.random() < 0.5:
                # Roommate household (2-5 members)
                size = min(random.randint(2, 5), len(remaining_users))
                members = remaining_users[:size]
                remaining_users = remaining_users[size:]
                
                household_name = f"{fake.street_name()} House"
                household_type = "roommates"
                
            elif len(remaining_users) >= 3 and random.random() < 0.3:
                # Friend group (3-6 members)
                size = min(random.randint(3, 6), len(remaining_users))
                members = remaining_users[:size]
                remaining_users = remaining_users[size:]
                
                household_name = f"{members[0].FirstName}'s Group"
                household_type = "friends"
                
            else:
                # Solo household
                members = [remaining_users[0]]
                remaining_users = remaining_users[1:]
                
                household_name = f"{members[0].FirstName}'s Home"
                household_type = "solo"
            
            # Create household
            household = Household(HouseholdName=household_name)
            session.add(household)
            session.flush()
            
            # Add members with appropriate roles
            if household_type == "family":
                # First two members are owners (parents)
                for i, user in enumerate(members):
                    role = owner_role if i < 2 else member_role
                    member = Member(
                        UserID=user.UserID,
                        HouseholdID=household.HouseholdID,
                        RoleID=role.RoleID
                    )
                    session.add(member)
            
            elif household_type == "roommates":
                # 1-2 members are owners
                num_owners = random.randint(1, 2)
                owners = random.sample(members, num_owners)
                for user in members:
                    role = owner_role if user in owners else member_role
                    member = Member(
                        UserID=user.UserID,
                        HouseholdID=household.HouseholdID,
                        RoleID=role.RoleID
                    )
                    session.add(member)
            
            else:
                # Friends or solo - first member is owner
                for i, user in enumerate(members):
                    role = owner_role if i == 0 else member_role
                    member = Member(
                        UserID=user.UserID,
                        HouseholdID=household.HouseholdID,
                        RoleID=role.RoleID
                    )
                    session.add(member)
            
            households.append((household, members, household_type))
            print(f"   Created {household_type} household: {household_name} ({len(members)} members)")
        
        session.commit()
        return households


class PantryPopulator:
    """Populates pantries with realistic item distributions"""
    
    @staticmethod
    def create_pantry(session, household):
        """Create pantry for household"""
        pantry = Pantry(
            HouseholdID=household.HouseholdID,
            PantryName=f"{household.HouseholdName} Pantry"
        )
        session.add(pantry)
        session.flush()
        return pantry
    
    @staticmethod
    def add_items_to_pantry(session, pantry, items, household_users):
        """Add items to pantry with realistic user additions"""
        # Each pantry gets 15-40 items
        num_items = random.randint(15, 40)
        selected_items = random.sample(items, min(num_items, len(items)))
        
        adds_records = []
        
        for item in selected_items:
            # Most items added by 1 person, occasionally 2-3
            roll = random.random()
            if roll < 0.7:
                num_adders = 1
            elif roll < 0.9:
                num_adders = 2
            else:
                num_adders = 3
            
            adders = random.sample(household_users, min(num_adders, len(household_users)))
            
            for user in adders:
                quantity = random.randint(1, 10)
                days_ago = random.randint(0, 60)
                date_added = datetime.date.today() - datetime.timedelta(days=days_ago)
                
                add = Adds(
                    UserID=user.UserID,
                    PantryID=pantry.PantryID,
                    ItemID=item.ItemID,
                    Quantity=quantity,
                    ItemInDate=date_added
                )
                adds_records.append(add)
        
        session.add_all(adds_records)
        session.commit()
        return adds_records


class RecipeManager:
    """Manages recipe creation and assignment"""
    
    @staticmethod
    def create_recipes(session, fathub_recipes, all_users):
        """Create global recipes from Fathub and custom recipes from users"""
        recipes = []
        
        print("   Adding Fathub recipes...")
        # Add Fathub recipes (global)
        for recipe_data in fathub_recipes:
            recipe = Recipe(
                RecipeName=recipe_data.get('name', 'Unnamed Recipe'),
                RecipeBody=recipe_data,
                Source='fathub',
                IsGlobal=True
            )
            session.add(recipe)
            session.flush()
            recipes.append(recipe)
        
        print("   Generating custom recipes from users...")
        # Each user creates 0-3 custom recipes
        for user in all_users:
            num_recipes = random.randint(0, 3)
            user_full_name = f"{user.FirstName} {user.LastName}"
            
            for _ in range(num_recipes):
                recipe_data = RealisticRecipeGenerator.generate_realistic_recipe(user_full_name)
                
                recipe = Recipe(
                    RecipeName=recipe_data['name'],
                    RecipeBody=recipe_data,
                    Source='custom',
                    IsGlobal=False
                )
                session.add(recipe)
                session.flush()
                recipes.append((recipe, user.UserID))  # Store tuple with creator
        
        session.commit()
        return recipes
    
    @staticmethod
    def assign_authors(session, recipes, households):
        """Assign authors to recipes with realistic patterns"""
        authors_records = []
        
        for recipe_info in recipes:
            # Handle both tuple (custom) and Recipe object (fathub)
            if isinstance(recipe_info, tuple):
                recipe, creator_user_id = recipe_info
                is_custom = True
            else:
                recipe = recipe_info
                creator_user_id = None
                is_custom = False
            
            if recipe.IsGlobal:
                # Global recipes: 1-3 random users author across random households
                num_household_authors = random.randint(1, 3)
                selected_households = random.sample(households, min(num_household_authors, len(households)))
                
                for household, household_users, _ in selected_households:
                    author_user = random.choice(household_users) if household_users else None
                    if author_user:
                        days_ago = random.randint(0, 365)
                        date_added = datetime.date.today() - datetime.timedelta(days=days_ago)
                        
                        author = Authors(
                            UserID=author_user.UserID,
                            HouseholdID=household.HouseholdID,
                            RecipeID=recipe.RecipeID,
                            DateAdded=date_added,
                            IsCustom=False
                        )
                        authors_records.append(author)
            
            else:
                # Custom recipe - created by specific user
                if creator_user_id:
                    # Find which households this user belongs to
                    user_households = [
                        (h, h_users) for h, h_users, _ in households 
                        if any(u.UserID == creator_user_id for u in h_users)
                    ]
                    
                    if user_households:
                        # Add to one of their households
                        household, household_users = random.choice(user_households)
                        
                        days_ago = random.randint(0, 180)
                        date_added = datetime.date.today() - datetime.timedelta(days=days_ago)
                        
                        author = Authors(
                            UserID=creator_user_id,
                            HouseholdID=household.HouseholdID,
                            RecipeID=recipe.RecipeID,
                            DateAdded=date_added,
                            IsCustom=True
                        )
                        authors_records.append(author)
        
        session.add_all(authors_records)
        session.commit()
        return authors_records
    
    @staticmethod
    def assign_recipes_to_households(session, recipes, households):
        """Assign recipes to households (Holds relationship)"""
        holds_records = []
        
        for household, household_users, household_type in households:
            # Each household holds 1-25 recipes
            num_recipes = random.randint(1, 25)
            
            # Extract recipe objects from tuples
            recipe_objects = []
            for r in recipes:
                if isinstance(r, tuple):
                    recipe_objects.append(r[0])
                else:
                    recipe_objects.append(r)
            
            selected_recipes = random.sample(recipe_objects, min(num_recipes, len(recipe_objects)))
            
            for recipe in selected_recipes:
                hold = Holds(
                    HouseholdID=household.HouseholdID,
                    RecipeID=recipe.RecipeID
                )
                holds_records.append(hold)
        
        session.add_all(holds_records)
        session.commit()
        return holds_records


def ensure_roles(session):
    """Ensure basic roles exist"""
    role_names = ["Owner", "Admin", "Member", "Viewer"]
    existing_roles = {r.RoleName: r for r in session.query(Role).all()}
    
    for role_name in role_names:
        if role_name not in existing_roles:
            role = Role(RoleName=role_name)
            session.add(role)
    
    session.commit()
    return session.query(Role).all()


def create_cross_household_edge_cases(session, all_users, households, items):
    """Create edge cases: users in multiple households, shared items"""
    
    print("   Creating multi-household memberships...")
    # Edge case 1: 10% of users belong to multiple households
    multi_household_users = random.sample(all_users, max(1, len(all_users) // 10))
    member_role = session.query(Role).filter_by(RoleName="Member").first()
    
    for user in multi_household_users:
        # Get current households
        current_households = session.query(Member).filter_by(UserID=user.UserID).all()
        current_household_ids = {m.HouseholdID for m in current_households}
        
        # Available households
        available_households = [
            h for h, _, _ in households 
            if h.HouseholdID not in current_household_ids
        ]
        
        if available_households:
            # Add to 1-2 additional households
            num_additional = random.randint(1, min(2, len(available_households)))
            additional_households = random.sample(available_households, num_additional)
            
            for household in additional_households:
                member = Member(
                    UserID=user.UserID,
                    HouseholdID=household.HouseholdID,
                    RoleID=member_role.RoleID
                )
                session.add(member)
    
    print("   Creating shared item edge cases...")
    # Edge case 2: Same items in multiple pantries by same user
    for user in random.sample(multi_household_users, min(5, len(multi_household_users))):
        user_households = session.query(Member).filter_by(UserID=user.UserID).all()
        
        if len(user_households) >= 2:
            item = random.choice(items)
            
            for member in user_households[:2]:
                household = session.query(Household).get(member.HouseholdID)
                pantry = household.pantry
                
                if pantry:
                    add = Adds(
                        UserID=user.UserID,
                        PantryID=pantry.PantryID,
                        ItemID=item.ItemID,
                        Quantity=random.randint(1, 5),
                        ItemInDate=datetime.date.today()
                    )
                    session.add(add)
    
    session.commit()
    print("✅ Created cross-household edge cases")


def populate_database(num_users):
    """Main population function"""
    
    print("🔧 Initializing database...")
    init_database()
    session = get_session()
    
    try:
        print("📋 Ensuring roles exist...")
        ensure_roles(session)
        
        print("🌐 Fetching external recipe data...")
        fetcher = DataFetcher()
        fathub_recipes = fetcher.fetch_fathub_recipes(limit=30)
        print(f"   Fetched {len(fathub_recipes)} recipes from Fathub")
        
        print("🥫 Generating realistic items from ingredient pool...")
        item_data_list = RealisticItemGenerator.generate_items()
        
        # Create items in database
        items = []
        for item_data in item_data_list:
            item = Item(
                ItemName=item_data['name'],
                ItemBody=json.dumps(item_data),
                Source=item_data['source'],
                IsGlobal=False  # Our custom ingredient pool
            )
            items.append(item)
        
        session.add_all(items)
        session.commit()
        print(f"✓ Created {len(items)} items in database")
        
        # Create users
        print(f"👥 Creating {num_users} users...")
        all_users = []
        
        for i in range(num_users):
            user = UserGenerator.create_user()
            session.add(user)
            session.flush()
            
            profile = UserGenerator.create_profile(user)
            session.add(profile)
            
            all_users.append(user)
            
            if (i + 1) % 10 == 0:
                print(f"   Created {i + 1}/{num_users} users...")
        
        session.commit()
        print(f"✓ Created {len(all_users)} users")
        
        # Create households organically
        print("🏠 Organizing users into households...")
        households = HouseholdOrganizer.create_households_from_users(session, all_users)
        print(f"✓ Created {len(households)} households")
        
        # Create pantries
        print("🗄️  Creating pantries...")
        for household, household_users, _ in households:
            pantry = PantryPopulator.create_pantry(session, household)
            PantryPopulator.add_items_to_pantry(session, pantry, items, household_users)
        print(f"✓ Created and populated {len(households)} pantries")
        
        # Create recipes
        print("📖 Creating recipes...")
        recipes = RecipeManager.create_recipes(session, fathub_recipes, all_users)
        print(f"✓ Created {len(recipes)} total recipes")
        
        print("✍️  Assigning recipe authors...")
        RecipeManager.assign_authors(session, recipes, households)
        
        print("📚 Assigning recipes to households...")
        RecipeManager.assign_recipes_to_households(session, recipes, households)
        
        print("📊 Creating nutrition logs...")
        log_count = 0
        for user in random.sample(all_users, min(len(all_users) // 2, 50)):
            logs = UserGenerator.create_nutrition_logs(user, days=random.randint(7, 30))
            session.add_all(logs)
            log_count += len(logs)
        session.commit()
        print(f"✓ Created {log_count} nutrition logs")
        
        print("🔀 Creating edge cases...")
        create_cross_household_edge_cases(session, all_users, households, items)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 DATABASE POPULATION SUMMARY")
        print("="*60)
        print(f"Users:              {session.query(User).count()}")
        print(f"User Profiles:      {session.query(UserProfile).count()}")
        print(f"Nutrition Logs:     {session.query(UserNutrition).count()}")
        print(f"Households:         {session.query(Household).count()}")
        
        # Count household types
        household_types = {}
        for _, _, h_type in households:
            household_types[h_type] = household_types.get(h_type, 0) + 1
        for h_type, count in household_types.items():
            print(f"  - {h_type.title()}:       {count}")
        
        print(f"Members:            {session.query(Member).count()}")
        print(f"Pantries:           {session.query(Pantry).count()}")
        print(f"Items:              {session.query(Item).count()}")
        print(f"Recipes:            {session.query(Recipe).count()}")
        print(f"  - Global:         {session.query(Recipe).filter_by(IsGlobal=True).count()}")
        print(f"  - Custom:         {session.query(Recipe).filter_by(IsGlobal=False).count()}")
        print(f"Authors:            {session.query(Authors).count()}")
        print(f"Adds:               {session.query(Adds).count()}")
        print(f"Holds:              {session.query(Holds).count()}")
        print("="*60)
        print("✅ Database population complete!")
        
    except IntegrityError as e:
        session.rollback()
        print(f"❌ Integrity error: {e}")
        raise
    except Exception as e:
        session.rollback()
        print(f"❌ Error populating database: {e}")
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Populate database with realistic test data"
    )
    parser.add_argument("--users", type=int, default=DEFAULT_USERS,
                       help=f"Number of users to generate (default: {DEFAULT_USERS})")
    
    args = parser.parse_args()
    
    print("🐵 MONKEYTYPE DATABASE POPULATOR 🐵")
    print("Realistic data generation for Kitchen Management Suite\n")
    
    populate_database(num_users=args.users)


if __name__ == "__main__":
    main()