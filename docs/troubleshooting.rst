.. _`Troubleshooting`:

Troubleshooting
===============
This section describes some common issues that can arise and possible solutions.

Issue #1: User Not Logged In After Login
-----------------------------------------

**Description**

After submitting the login form, the user is not authenticated. The session variables (logged_in, user_id) are not being set, and the user is redirected back to the login page instead of the dashboard.

**Solution**

1. **Check Database Connection:**
   - Verify PostgreSQL is running: ``psql -U postgres -d kitchen_db -c "SELECT 1;"``
   - Confirm connection URI in .env file matches your database setup
   - Check Flask logs for database connection errors

2. **Verify User Exists:**
   - Query the database to confirm the user exists:
   
   .. code-block:: sql
   
      SELECT UserID, Username, Email FROM "user" WHERE Username = 'your_username';

3. **Check Password Hashing:**
   - Ensure the password was hashed when the account was created
   - Verify the check_password_hash() function is working correctly
   - Test manually in Python:
   
   .. code-block:: python
   
      from werkzeug.security import generate_password_hash, check_password_hash
      hashed = generate_password_hash('testpass')
      print(check_password_hash(hashed, 'testpass'))  # Should return True

4. **Session Configuration:**
   - Verify app.secret_key is set in app.py
   - Ensure cookies are enabled in your browser
   - Clear browser cache and cookies, then try logging in again

5. **Check Login Route:**
   - Verify the login route in src/blueprints/auth.py is correctly setting session variables
   - Add debug prints to trace execution flow

Issue #2: 404 Not Found Error on Navigation Links
---------------------------------------------------

**Description**

Clicking navigation links (e.g., Kitchen, Account, Pantry) returns a 404 error. The href attributes use relative paths like ``./kitchen.html`` instead of Flask routes.

**Solution**

1. **Use url_for() in Templates:**
   - Replace direct href links with Flask's url_for() function:
   
   .. code-block:: html
   
      <!-- Incorrect -->
      <a href="./kitchen.html">Kitchen</a>
      
      <!-- Correct -->
      <a href="{{ url_for('pantry.pantry_view') }}">Kitchen</a>

2. **Define Flask Routes:**
   - Ensure each page has a corresponding Flask route defined in the blueprints:
   
   .. code-block:: python
   
      @pantry_bp.route('/pantry')
      def pantry_view():
          return render_template('pantry.html', ...)

3. **Check Blueprint Registration:**
   - Verify all blueprints are registered in app.py:
   
   .. code-block:: python
   
      app.register_blueprint(pantry_bp)
      app.register_blueprint(recipes_bp)
      app.register_blueprint(calorie_tracker_bp)

4. **List Available Routes:**
   - Run ``flask routes`` to see all registered routes
   - Verify the route names match the url_for() calls in templates

Issue #3: Database Query Returns None or Empty Results
-------------------------------------------------------

**Description**

A database query that should return data is returning None or an empty list. For example, querying UserNutrition for a user's calorie data returns no results.

**Solution**

1. **Verify User ID is Correct:**
   - Check that session['user_id'] contains a valid value:
   
   .. code-block:: python
   
      user_id = session.get('user_id')
      print(f"User ID: {user_id}")
      if not user_id:
          return "User not logged in", 401

2. **Check Database Schema:**
   - Verify the table and column names match exactly (case-sensitive):
   
   .. code-block::
    
        SELECT * FROM user_nutrition LIMIT 1;
        \d user_nutrition;  -- Describes table structure

3. **Inspect the SQLAlchemy Model:**
   - Ensure the model class has attributes matching the database columns:
   
   .. code-block:: python
   
      class UserNutrition(Base):
          __tablename__ = 'user_nutrition'
          id = Column(Integer, primary_key=True)
          UserID = Column(Integer, ForeignKey('user.UserID'))
          Date = Column(Date)
          CaloriesConsumed = Column(Integer)

4. **Debug the Query:**
   - Print the generated SQL query:
   
   .. code-block:: python
   
      query = db_session.query(UserNutrition).filter(
          UserNutrition.UserID == user_id
      )
      print(query)  # Prints the SQL
      result = query.first()
      print(f"Result: {result}")

5. **Use .all() Instead of .first():**
   - If expecting multiple rows, use .all() instead of .first():
   
   .. code-block:: python
   
      nutrition_data = db_session.query(UserNutrition).filter(
          UserNutrition.UserID == user_id
      ).all()  # Returns list

6. **Check Data Existence:**
   - Verify data actually exists in the database for the given user:
   
   .. code-block:: sql
   
      SELECT * FROM user_nutrition WHERE "UserID" = <your_user_id>;

Issue #4: Flask Session Not Persisting Between Requests
-------------------------------------------------------

**Description**

Session variables (e.g., user_id, current_household_id) are lost after the first request. The user is logged in on one page but appears logged out on the next page.

**Solution**

1. **Set Secret Key:**
   - Ensure app.secret_key is configured in app.py:
   
   .. code-block:: python
   
      app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

2. **Check .env File:**
   - Verify SECRET_KEY is set in .env:
   
   .. code-block:: bash
   
      SECRET_KEY=your-long-random-secret-key-here

3. **Enable Cookies in Browser:**
   - Ensure cookies are enabled (session storage relies on cookies)
   - Check browser settings: Settings → Privacy & Security → Cookies

4. **Session Configuration:**
   - Verify Flask session settings (optional, default is fine for most use cases):
   
   .. code-block:: python
   
      app.config['SESSION_COOKIE_SECURE'] = True  # Only over HTTPS
      app.config['SESSION_COOKIE_HTTPONLY'] = True  # JavaScript cannot access
      app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

5. **Check Session Usage:**
   - Ensure you're using the same session object throughout:
   
   .. code-block:: python
   
      from flask import session
      session['user_id'] = user.UserID  # Set
      user_id = session.get('user_id')  # Get

6. **Test in Incognito Mode:**
   - Open browser incognito/private window to rule out cookie conflicts

Issue #5: Docker Container Cannot Connect to PostgreSQL
-------------------------------------------------------

**Description**

Flask application running in Docker cannot connect to PostgreSQL. Error: "could not connect to server: Connection refused" or "Name or service not known".

**Solution**

1. **Check Docker Compose Service Names:**
   - Ensure the hostname in the connection URI matches the service name in docker-compose.yml:
   
   .. code-block:: yaml
   
      services:
        db:
          image: postgres:13
          environment:
            POSTGRES_PASSWORD: password
            POSTGRES_DB: kitchen_db

   .. code-block:: python
   
      # Use 'db' as hostname (the service name)
      DATABASE_URL = 'postgresql://postgres:password@db:5432/kitchen_db'

2. **Verify PostgreSQL is Running:**
   - Check Docker logs: ``docker-compose logs db``
   - Ensure container is healthy: ``docker-compose ps``

3. **Check Network:**
   - Verify both Flask and PostgreSQL containers are on the same network:
   
   .. code-block:: bash
   
      docker network ls
      docker inspect <network_name>

4. **Test Connection from Flask Container:**
   - Enter Flask container and test PostgreSQL:
   
   .. code-block:: bash
   
      docker-compose exec web bash
      psql -h db -U postgres -d kitchen_db -c "SELECT 1;"

5. **Environment Variables:**
   - Verify .env file is loaded and matches docker-compose.yml values
   - Check that load_dotenv() is called in app.py

6. **Port Mapping:**
   - Ensure ports are correctly mapped in docker-compose.yml:
   
   .. code-block:: yaml
   
      services:
        db:
          ports:
            - "5432:5432"
        web:
          ports:
            - "5000:5000"