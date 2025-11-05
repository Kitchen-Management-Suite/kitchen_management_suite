"""
File: food_log.py
File-Path: src/db/schema/holds.py
Author: Noah Yurasko
Date-Created: 11/4/2025

Description:
    SQLAlchemy ORM model for food log, tracks individual meals 
    and food items tracked by usters

Inputs:
    SQLAlchemy types/relationship helpers and the declarative Base
    and other ORM models (User, UserNutrition)

Outputs:
    The mapped `FoodLog` class usable with SQLAlchemy sessions and __repr__ for debug
"""

from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from db.server import Base

class FoodLog(Base):
    """class for the FoodLog entity containing users food log"""
    __tablename__ = "FoodLog"

    LogId = Column(Integer, primary_key=True, autoincrement=True)
    NutritionId = Column(Integer, ForeignKey("UserNutrition.NutritionID"), nullable=False)
    Name = Column(String(100))
    Barcode = Column(Integer)
    TypeOfMeal = Column(String(10))
    Picture = Column(String(50))#We can decide if we want to keep this later
    MacroNutrients = Column(String(100))
    #We may want to simply use the name to get the item from open food facts
    #And not store all the nutrients, as there was be ALOT of redundent data 
    # relationships
    user_nutrition = relationship("UserNutrition", back_populates="foodlog")

    def __repr__(self):
        return f"""
        FOODLOG: LOGID {self.LogId} for day of {user_nutrition.Date}
        """