"""
File: join_request.py
File-Path: src/db/schema/join_request.py
Author: Assistant
Date-Created: 12-04-2025

Description:
    SQLAlchemy ORM model for the JoinRequest entity ('JoinRequests' table).
    Tracks pending requests from users wanting to join a household.

Inputs:
    SQLAlchemy types/relationship helpers and the declarative Base
    and other ORM models (User, Household)

Outputs:
    The mapped `JoinRequest` class usable with SQLAlchemy sessions
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.server import Base


class JoinRequest(Base):
    """Class for the join request table"""
    __tablename__ = 'JoinRequests'

    RequestID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey('Users.UserID'), nullable=False)
    HouseholdID = Column(Integer, ForeignKey('Households.HouseholdID'), nullable=False)
    Status = Column(String(20), default='pending')  # pending, accepted, denied
    Message = Column(Text, nullable=True)  # Optional message from user
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, onupdate=func.now())

    # relationships
    user = relationship("User", back_populates="join_requests")
    household = relationship("Household", back_populates="join_requests")

    def __repr__(self):
        return f"""
        JOIN REQUEST: User {self.UserID} -> Household {self.HouseholdID} ({self.Status})
        """

