"""
File: __init__.py
Author: Rohan Plante
Date-Created: 10/16/2025
"""
# import all tables (models) so they get registered with Base.metadata
from .user import User
from .user_profile import UserProfile
from .user_nutrition import UserNutrition
from .role import Role
from .household import Household
from .pantry import Pantry
from .item import Item
from .recipe import Recipe
from .member import Member
from .adds import Adds
from .authors import Authors
from .holds import Holds
from .join_request import JoinRequest

# make tables (models) available when importing from schema package
__all__ = [
    'User', 
    'UserProfile', 
    'UserNutrition', 
    'Role', 
    'Household', 
    'Pantry', 
    'Item', 
    'Recipe', 
    'Member', 
    'Adds', 
    'Authors', 
    'Holds',
    'JoinRequest'
]