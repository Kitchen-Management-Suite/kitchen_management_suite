"""
File: user.py
File-Path: src/db/schema/user.py
Author: Thomas Bruce, Rohan Plante
Date-Created: 09-30-2025

Description:
    SQLAlchemy ORM model for the User entity ('Users' table).

Inputs:
    SQLAlchemy types/relationship helpers and the declarative Base
    and other ORM models (Household, Recipe, Member)

Outputs:
    The mapped `User` class usable with SQLAlchemy sessions and __repr__ for debug
"""

# TODO:
# - hash all user values
# - deal with UUIDv4 for UserID

from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship
from db.server import Base

class User(Base):
    """class for the user table"""
    __tablename__ = 'Users'

    UserID = Column(Integer, primary_key=True, autoincrement=True)
    FirstName = Column(String(50))
    LastName = Column(String(50))
    Username = Column(String(50), unique=True)
    Email = Column(String(100))
    DateOfBirth = Column(Date)
    Password = Column(String(255))

    # relationships to junction tables
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    nutrition_logs = relationship("UserNutrition", back_populates="user")
    members = relationship("Member", back_populates="user")
    adds = relationship("Adds", back_populates="user")
    authors = relationship("Authors", back_populates="user")
    join_requests = relationship("JoinRequest", back_populates="user", cascade="all, delete-orphan")
    
    households = relationship("Household", secondary="Members", viewonly=True)
    items = relationship("Item", secondary="Adds", viewonly=True)
    recipes = relationship("Recipe", secondary="Authors", viewonly=True)

    def __repr__(self):
        return f"""
        USER: {self.Username}, NAME: {self.FirstName} {self.LastName}, EMAIL: {self.Email}
        """
