"""
File: server.py
File-Path: src/db/server.py
Author: Thomas Bruce, Rohan Plante
Date-Created: 09-29-2025

Description:
    Postgres connection handler

Inputs:
    - .env
    - postgres connection

Outputs:
    - postgres connection
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# load env
load_dotenv()

DB_USER = os.getenv("db_owner")
DB_PASS = os.getenv("db_pass")
DB_NAME = os.getenv("db_name")
DB_HOST = os.getenv("db_host", "localhost")
DB_PORT = os.getenv("db_port", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# sqlalchemy
engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_session():
    """Get a database session"""
    return SessionLocal()

def init_database():
    """Initialize database tables"""
    try:
        # import all of the tables
        from db.schema import Adds, Authors, Holds, Household, Item, Member, Pantry, Recipe, Role, User, UserNutrition, UserProfile
        # create all of the tables
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print(f"\n\n----------- Connection successful!")
        print(f" * Connected to database: {DB_NAME}")
        print(f" * Database tables created successfully!")
        return True

    # print the error if the connection attempt fails
    except Exception as error:
        print(f"\n\n----------- Connection failed!")
        print(f" * Unable to connect to database: {DB_NAME}")
        print(f" * ERROR: {error}")
        return False

# we can kinda just copy over the init from lab 4 for creating it, but over
# there it is specific to the tables for the lab, so i omitted it for brevity
# have no fear thomas, the init has been made :)
