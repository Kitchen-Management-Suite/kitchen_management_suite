.. _`Resources`:

Resources
=========
This section describes classes and functions private to |appname|. It is intended to document how the application works

Application Overview
--------------------

The **Kitchen Management Suite (KMS)** is a Flask-based web application designed to help households manage their pantry, recipes, and nutrition tracking. The application is built using:

- **Backend:** Flask (Python web framework)
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Frontend:** Jinja2 templates with HTML/CSS/JavaScript
- **Architecture:** Blueprint-based modular design with helper functions

How the Application Runs
------------------------

Startup Flow
~~~~~~~~~~~~

1. **Initialization (src/app.py)**
   - Flask application is instantiated with a secret key loaded from environment variables (.env).
   - Database is initialized via init_database(), which creates all SQLAlchemy tables if they don't exist.
   - All database schemas are imported to register models with SQLAlchemy's Base.

2. **Blueprint Registration**
   Six modular blueprints are registered with the Flask app:
   - auth_bp — User authentication (login, register, logout)
   - recipes_bp — Recipe management
   - pantry_bp — Pantry item management
   - calorie_tracker_bp — Nutrition tracking
   - manage_user_profile_bp — User profile management
   - settings_bp — Application settings

3. **Context Processor**
   - The inject_navbar() function is registered as a context processor.
   - It injects navbar data (user info, household selection, roles) into every template automatically.

4. **Server Start**
   - Flask development server starts and listens for incoming HTTP requests.
   - Session management is handled via Flask's session object (cookie-based or server-side).

Core Database Schema (Classes)
------------------------------

All database models are defined in src/db/schema and use SQLAlchemy ORM.

Primary Entities
~~~~~~~~~~~~~~~~

**User** (src/db/schema/user.py)
   Stores user account information
   
   - UserID (Primary Key)
   - Username
   - Email
   - Password (hashed)
   - DateOfBirth

**Household** (src/db/schema/household.py)
   Represents a household (family/group)
   
   - HouseholdID (Primary Key)
   - HouseholdName
   - JoinCode (unique identifier for joining)

**Recipe** (src/db/schema/recipe.py)
   Stores recipes (global or custom)
   
   - RecipeID (Primary Key)
   - RecipeName
   - RecipeBody (JSON format)
   - IsGlobal (boolean flag)

**Item** (src/db/schema/item.py)
   Represents pantry items (ingredients)
   
   - ItemID (Primary Key)
   - ItemName
   - Calories
   - Carbs
   - Protein
   - Fat

**Pantry** (src/db/schema/pantry.py)
   Links items to household pantries
   
   - PantryID (Primary Key)
   - HouseholdID (Foreign Key)

**UserNutrition** (src/db/schema/user_nutrition.py)
   Tracks daily nutrition logs per user
   
   - UserID (Foreign Key)
   - Date
   - CaloriesConsumed
   - Carbs
   - Protein
   - Fat

**UserProfile** (src/db/schema/user_profile.py)
   Extended user profile information
   
   - UserID (Primary Key)
   - DailyCalorieGoal
   - PreferredMeasure

Junction Tables (Many-to-Many Relationships)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Member** (src/db/schema/member.py)
   User ↔ Household relationship
   
   - Tracks household membership and user roles

**Authors** (src/db/schema/authors.py)
   User ↔ Recipe relationship
   
   - Tracks who authored/created recipes

**Holds** (src/db/schema/holds.py)
   Household ↔ Recipe relationship
   
   - Tracks which recipes belong to a household

**Adds** (src/db/schema/adds.py)
   User ↔ Item relationship
   
   - Tracks which items users added to the pantry

**JoinRequest** (src/db/schema/join_request.py)
   User → Household relationship
   
   - Pending household join requests

Supporting Entities
~~~~~~~~~~~~~~~~~~~

**Role** (src/db/schema/role.py)
   Defines user roles within households (Admin, Member, Moderator, etc.)

Key Functions & Flow
--------------------

Database Access Layer (src/db/server.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def get_session():
       """Returns a new SQLAlchemy session for database operations"""
       
   def init_database():
       """Creates all tables in PostgreSQL if they don't exist"""

**Connection Details:**

- PostgreSQL connection URI constructed from environment variables: postgresql://db_owner:db_pass@db_host:5432/db_name
- SQLAlchemy engine uses echo=True for debugging (logs SQL queries to console)

Authentication Flow (src/blueprints/auth.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Register Route (/register)**

1. User submits registration form (username, email, password, DOB)
2. Validation checks occur via validate_registration_data()
3. Check if username or email already exists in database
4. Hash password using werkzeug.security.generate_password_hash()
5. Create new User object and commit to database
6. Log authentication event via log_auth()
7. Redirect to login page

**Login Route (/login)**

1. User submits login form (username/email, password)
2. Validate input via validate_login_data()
3. Query database for user matching username or email
4. Verify password hash using check_password_hash()
5. Set Flask session variables:
   - session['logged_in'] = True
   - session['user_id'] = user.UserID
6. Redirect to index or requested page

**Logout Route (/logout)**

1. Clear Flask session
2. Redirect to login page

Index Route (/ in src/app.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a logged-in user visits the home page:

1. **Check Login Status**
   - Verify session['logged_in'] is True
   - Retrieve user_id and current_household_id from session

2. **Query Metrics**
   - Fetch all households the user belongs to via Member table
   - Fetch current household details
   - Count pantry items, recipes, household members
   - Fetch expiring items, suggested recipes, recent activity

3. **Render Dashboard**
   - Pass metrics dictionary to index.html template
   - Jinja2 renders the dashboard with user data

**Example Metrics Collected:**

.. code-block:: python

   metrics = {
       'total_households': len(user_households),
       'current_household': current_household_obj,
       'pantry_items_count': count_of_items,
       'household_recipes_count': count_of_recipes,
       'household_members_count': count_of_members,
       'suggested_recipes': list_of_recipes,
       'expiring_soon': list_of_expiring_items,
       'shopping_list': list_of_needed_items,
       'top_contributors': list_of_users
   }

Pantry Management (/pantry)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Query Pantry and Item tables for current household
2. Display all items with expiration dates
3. Allow users to add/remove items via forms
4. Calculate nutritional totals for the household

Recipe Management (/recipes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Query Recipe and Holds tables for household recipes
2. Fetch recipe details from RecipeBody (JSON column)
3. Display global recipes (from Fathub dataset) and custom recipes
4. Allow users to author new recipes (Authors table)
5. Suggest recipes based on available pantry items

Calorie Tracking (/calorieTracking)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Query UserNutrition table for logged-in user's nutrition logs
2. Group meals by type (Breakfast, Lunch, Dinner, Snacks)
3. Calculate daily totals vs. user's daily_calorie_goal (from UserProfile)
4. Display progress bar and macronutrient breakdown
5. Allow users to log meals (add items to nutrition log)

Household Management
~~~~~~~~~~~~~~~~~~~~

**Create Household (POST /household/create)**

1. User submits household creation form
2. Create new Household object
3. Create Member record linking user to household with admin role
4. Generate unique JoinCode via Household.generate_join_code()
5. Commit to database

**Join Household (POST /household/join)**

1. User submits household name or join code
2. Look up household by code or name
3. Create JoinRequest (pending) or directly add Member (if code is valid)
4. Set user's role (typically "Member" by default)

**Switch Household (GET /household/switch/<id>)**

1. Update session['current_household_id'] to the new household
2. Redirect to index to show new household's data

Helper Functions (src/helpers)
------------------------------

**src/helpers/navbar_helper.py**
   - get_user_households() — Retrieves all households for a user
   - inject_navbar_context() — Injects user, household, and role data into all templates

**validation_helper.py**
   - validate_registration_data() — Client-side and server-side input validation
   - validate_login_data() — Validates login credentials

**logging_helper.py**
   - log_auth() — Logs authentication events for debugging

**api_helper.py**
   - API response utilities for formatting JSON responses for API calls

**unit_converter.py**
   - Unit conversion functions (e.g., cups → grams)

Session Management
------------------

The application distinguishes between two session types:

1. **Flask Session (session)**
   - Stores user-specific data: logged_in, user_id, current_household_id, username
   - Persisted in cookies (or server-side, depending on config)
   - Used for tracking login state and user context across requests

2. **SQLAlchemy Session (get_session())**
   - Manages database connections and transactions
   - Created fresh per request or per operation
   - Used to query, insert, update, and delete data in PostgreSQL

Frontend Architecture
---------------------

**Templates** (src/templates)

- index.html — Dashboard
- calorieTracking.html — Nutrition tracker
- pantry.html — Pantry manager
- recipes.html — Recipe browser
- Base template with navbar injection

**Static Files** (src/static)

- navbar.js — Household switching, dropdown menus
- pantry.js — Add/remove items
- recipes.js — Filter, search, select recipes
- calorieTrack.js — Log meals, update nutrition data
- CSS files for styling

Environment Variables (.env)
-----------------------------

.. code-block:: bash

   SECRET_KEY=your-secret-key-here
   db_owner=postgres_username
   db_pass=postgres_password
   db_name=kitchen_db
   db_host=localhost
   db_port=5432

Data Flow Example: Logging a Meal
----------------------------------

1. **User clicks "Add Meal" button** on /calorieTracking page
2. **JavaScript** sends api request to /meal_item_search with meal type and food search query
3. **Backend** (blueprint) queries Item table and returns matching food items
4. **User selects an item** and submits quantity
5. **Backend** calculates nutrition values and creates/updates UserNutrition record for today
6. **Dashboard updates** to reflect new daily totals

Error Handling
--------------

- **Database Errors:** Caught in try/except blocks; session is rolled back on failure
- **Authentication Errors:** Flash messages displayed; user redirected to login
- **Validation Errors:** Flash messages for each failed field
- **Logging:** All errors logged via logging_helper.py for debugging

Summary
-------

This architecture allows the KMS to manage multiple households, track nutrition, manage recipes, and coordinate household members—all with a clean separation of concerns between authentication, data access, business logic, and presentation layers.

