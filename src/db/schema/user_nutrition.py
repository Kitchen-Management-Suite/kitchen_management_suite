"""
File: user_nutrition.py
File-Path: src/db/schema/user_nutrition.py
Author: Rohan Plante
Date-Created: 10/23/2025

Description:
    SQLAlchemy ORM model for the UserNutrition entity ('UserNutrition' table).
    Stores calorie and macronutrient data per user.
    Allows daily tracking/logging and dietary goal management.

Inputs:
    SQLAlchemy types/relationship helpers and the declarative Base

Outputs:
    The mapped `UserNutrition` class usable with SQLAlchemy sessions and __repr__ for debug
"""

from sqlalchemy import Column, Integer, Float, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from db.server import Base

class UserNutrition(Base):
    """class for the user nutrition tracking table"""
    __tablename__ = 'UserNutrition'

    NutritionID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey('Users.UserID'), nullable=False)
    Date = Column(Date, nullable=False)
    Time = Column(Time)
    CaloriesConsumed = Column(Integer)
    # all metrics in grams !!! sodium in mg
    Protein = Column(Float)
    Carbs = Column(Float)
    Fat = Column(Float)
    Fiber = Column(Float)
    Sugar = Column(Float)
    Sodium = Column(Float)  

    # relationship
    user = relationship("User", back_populates="nutrition_logs")
    foodlog = relationship("FoodLog", back_populates="user_nutrition")

    def __repr__(self):
        return f"NUTRITION LOG for UserID: {self.UserID}, Date: {self.Date}, Calories: {self.CaloriesConsumed}"