"""
File: adds.py
File-Path: src/db/schema/adds.py
Author: Rohan Plante
Date-Created: 10-15-2025

Description:
    SQLAlchemy ORM model for the Adds relationship ("Adds" table).
    Junction table connecting Users, Items, and Pantries.
    Tracks who added what to where and when.

Inputs:
    SQLAlchemy types/relationship helpers and the declarative Base
    and other ORM models (User, Item, Pantry)

Outputs:
    The mapped `Adds` class usable with SQLAlchemy sessions and __repr__ for debug
"""

from sqlalchemy import Column, Integer, Date, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from db.server import Base

class Adds(Base):
    """class for the adds junction table"""
    __tablename__ = "Adds"

    AddsID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey("Users.UserID"), nullable=False)
    PantryID = Column(Integer, ForeignKey("Pantries.PantryID"), nullable=False)
    ItemID = Column(Integer, ForeignKey("Items.ItemID"), nullable=False)
    Quantity = Column(Float)  # Changed from Integer to Float for fractional amounts
    Unit = Column(String(50))  # e.g., 'pieces', 'lbs', 'cups', 'sticks', etc.
    ItemInDate = Column(Date)

    # relationships
    user = relationship("User", back_populates="adds")
    pantry = relationship("Pantry", back_populates="adds")
    item = relationship("Item", back_populates="adds")

    def __repr__(self):
        return f"""
        ADDS: UserID {self.UserID} added ItemID {self.ItemID} to PantryID {self.PantryID}, Qty: {self.Quantity}
        """