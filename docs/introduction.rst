.. _`Introduction`:

Introduction
============

**Kitchen Management Suite (KMS)** is a comprehensive household kitchen management application designed to help families and groups coordinate pantry inventory, manage recipes, and track daily nutrition intake. Built with Flask, PostgreSQL, and Jinja2 templates, KMS provides an intuitive interface for managing shared kitchen resources across multiple household members.

What is KMS?
------------

Kitchen Management Suite is an all-in-one solution for:

- **Pantry Management** — Track ingredients in your household pantry with expiration dates and nutritional information
- **Recipe Management** — Create, store, and share recipes within your household or browse from a global recipe database
- **Nutrition Tracking** — Log daily meals and monitor caloric intake against personal goals
- **Household Coordination** — Invite household members, assign roles, and manage permissions
- **User Accounts** — Secure, multi-user authentication with household-specific data isolation

Key Features
~~~~~~~~~~~~

- **Multi-Household Support** — Users can belong to multiple households and switch between them seamlessly
- **Role-Based Access Control** — Assign roles (Admin, Member, Moderator) with appropriate permissions
- **Shared Pantry Inventory** — All household members can view and add items to the shared pantry
- **Personalized Nutrition Goals** — Each user has custom daily calorie targets and dietary preferences
- **Recipe Suggestions** — Get recipe recommendations based on available pantry items

Technology Stack
----------------

**Backend**
   - Flask (Python web framework)
   - SQLAlchemy ORM for database operations
   - PostgreSQL for persistent data storage
   - Werkzeug for secure password hashing

**Frontend**
   - Jinja2 templating engine for server-side rendering
   - HTML5 for markup structure
   - CSS for styling and layout
   - Vanilla JavaScript for client-side interactivity (form handling, DOM manipulation)
   - Custom VirtualDOM Implementation 

**Architecture**
   - Blueprint-based modular design for scalability
   - Helper functions for cross-cutting concerns (authentication, validation, logging)
   - Session-based user authentication
   - Context processors for template variable injection

Who Should Use KMS?
~~~~~~~~~~~~~~~~~~~

KMS is ideal for:

- **Families** sharing a kitchen and meal planning responsibilities
- **Roommate Groups** coordinating grocery shopping and cooking
- **Small Communities** managing shared resources
- **Health-Conscious Individuals** tracking nutritional intake
- **Home Cooks** organizing recipes and pantry inventory

Getting Started
---------------

Installation
~~~~~~~~~~~~

1. **Clone the Repository**

   .. code-block:: bash

      git clone https://github.com/Kitchen-Management-Suite/kitchen_management_suite.git
      cd kitchen_management_suite

2. **Set Up Environment**

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate
      pip install -r requirements.txt

3. **Configure Database**

   Create a ``.env`` file in the project root:

   .. code-block:: bash

      SECRET_KEY=your-secret-key-here
      db_owner=postgres
      db_pass=your_password
      db_name=kitchen_db
      db_host=localhost
      db_port=5432

4. **Initialize Database**

   .. code-block:: bash

      flask db init
      flask db migrate -m "Initial migration"
      flask db upgrade

5. **Run the Application**

   .. code-block:: bash

      flask run

   Access the application at ``http://localhost:5000``

Docker Setup
~~~~~~~~~~~~

Alternatively, run KMS using Docker:

.. code-block:: bash

   docker-compose up --build

This will start both the Flask application and PostgreSQL database.

User Workflows
--------------

**For New Users**

1. Register a new account with email and password
2. Create a household or join an existing one using a join code
3. Set your daily calorie goal and dietary preferences
4. Start exploring the pantry and recipes

**For Household Admins**

1. Create or manage household settings
2. Invite members via join codes
3. Assign roles and permissions
4. Monitor household activity and shopping lists

**For Daily Users**

1. View pantry inventory and check expiration dates
2. Log meals and track daily calories
3. Browse or create recipes
4. Contribute items to the household pantry

Documentation Structure
-----------------------

This documentation is organized as follows:

- **Introduction** (this page) — Overview and getting started
- **Resources** — Complete API reference, database schema, and architecture details
- **Troubleshooting** — Common issues and solutions
- **Development** — Contributing guidelines and development setup

Next Steps
----------

- Read the **Resources** section to understand how the application works internally
- Check **Troubleshooting** if you encounter any issues
- Explore the codebase in ``src/`` directory
- Join our GitHub discussions for questions and feature requests

Github Repository
-----------------

For source code, issues, and contributions, visit:

* `Kitchen Management Suite on GitHub <https://github.com/Kitchen-Management-Suite/kitchen_management_suite>`_

License
-------

This project is licensed under the BSD 4-Clause  License. See LICENSE file for details.

Social Contract
---------------

We are committed to maintaining a respectful and inclusive community. See SOCIAL_CONTRACT.md for our code guidelines.