"""
File: household.py
File-Path: src/db/schema/household.py
Author: Rohan Plante, Thomas Bruce
Date-Created: 09-30-2025

Description:
    SQLAlchemy ORM model for the Household entity ('Households' table).

Inputs:
    SQLAlchemy types/relationship helpers and the declarative Base
    and other ORM models (Recipe, User)

Outputs:
    The mapped `Household` class usable with SQLAlchemy sessions and __repr__ for debug
"""
import secrets
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from db.server import Base

class Household(Base):
    """class for the household table"""
    __tablename__ = 'Households'

    HouseholdID = Column(Integer, primary_key=True, autoincrement=True)
    HouseholdName = Column(String(100), nullable=False)
    JoinCode = Column(String(12), unique=True, nullable=True)
    JoinCodeEnabled = Column(Boolean, default=False)

    # relationships
    pantry = relationship("Pantry", back_populates="household", uselist=False)
    members = relationship("Member", back_populates="household")
    authors = relationship("Authors", back_populates="household")
    holds = relationship("Holds", back_populates="household")
    join_requests = relationship("JoinRequest", back_populates="household", cascade="all, delete-orphan")
    
    users = relationship("User", secondary="Members", viewonly=True)
    recipes = relationship("Recipe", secondary="Holds", viewonly=True)

    def generate_join_code(self):
        """Generate a new unique join code"""
        self.JoinCode = secrets.token_urlsafe(8)[:8].upper()
        return self.JoinCode
    
    def __repr__(self):
        return f"""
        HOUSEHOLD: {self.HouseholdName} (ID: {self.HouseholdID})
        """
