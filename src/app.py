"""
File: app.py
File-Path: src/app.py
Author: Thomas Bruce
Date-Created: 09-29-2025

Description:
    Base of Flask app

Inputs:
    auth blueprint
    db schemas


Outputs:
    serves flask server
    inits db
"""

import os
from flask import Flask, render_template, session
from dotenv import load_dotenv

# load environment variables
load_dotenv()

from db.server import engine, Base, init_database

# schema imports
from db.schema import adds, authors, holds, household, item, member, pantry, recipe, role, user_nutrition, user_profile, user

# auth blueprint import
from auth import auth_bp

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# initialize database tables
with app.app_context():
    print("initializing database...")
    init_database()

# register auth blueprint
app.register_blueprint(auth_bp)

@app.route("/")
def index():
    """handle index route"""
    if session.get('logged_in'):
        return render_template("index.html")
    else:
        return render_template("public.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
