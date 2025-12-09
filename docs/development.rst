.. _`Development`:

Development
===========

This section is intended for developers who want to contribute fixes, enhancements, or new features to the Kitchen Management Suite.

Code of Conduct
---------------

All contributors must adhere to our community guidelines as outlined in `SOCIAL_CONTRACT.md <../../SOCIAL_CONTRACT.md>`_. Key principles include:

- Respect and inclusivity for all contributors
- Constructive feedback and collaboration
- Adherence to project coding conventions
- Transparency in decision-making

Repository
----------

The Kitchen Management Suite repository is hosted on GitHub:

* `Kitchen Management Suite on GitHub <https://github.com/Kitchen-Management-Suite/kitchen_management_suite>`_

Setting Up Your Development Environment
----------------------------------------

Prerequisites
~~~~~~~~~~~~~

Ensure you have the following installed:

- **Python 3.8+** — Check with ``python --version``
- **PostgreSQL 12+** — Download from `postgresql.org <https://www.postgresql.org/>`_
- **Git** — For version control
- **Docker & Docker Compose** (optional) — For containerized development

Clone the Repository
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    git clone https://github.com/Kitchen-Management-Suite/kitchen_management_suite.git
    cd kitchen_management_suite

Create a Python Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A Python virtual environment is required to isolate project dependencies:

.. code-block:: bash

    # Create virtual environment
    python -m venv venv

    # Activate it
    # On Linux/macOS:
    source venv/bin/activate
   
    # On Windows:
    venv\Scripts\activate

Install Dependencies
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install -r requirements.txt

Configure Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a ``.env`` file in the project root with your local configuration:

.. code-block:: bash

    SECRET_KEY=your-development-secret-key-here
    db_owner=postgres
    db_pass=your_local_db_password
    db_name=kitchen_db_dev
    db_host=localhost
    db_port=5432

Initialize the Database
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    python src/app.py

    # Or manually initialize via Flask CLI:
    export FLASK_APP=src/app.py
    flask shell
    >>> from db.server import init_database, engine, Base
    >>> init_database()
    >>> exit()

Run the Application
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # From the project root
    python -m flask --app src.app run

    # Or with debug mode enabled (auto-reload on file changes):
    python -m flask --app src.app run --debug

The application will be available at ``http://localhost:5000``

Running with Docker (Alternative)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you prefer containerized development:

.. code-block:: bash

    docker-compose up --build

This starts both Flask and PostgreSQL containers. Access at ``http://localhost:5000``

Code Organization
~~~~~~~~~~~~~~~~~

Keep code modular and organized:

- **Database models** → ``src/db/schema/``
- **Routes and handlers** → ``src/blueprints/``
- **Utilities and helpers** → ``src/helpers/``
- **Templates** → ``src/templates/``
- **Static assets** → ``src/static/``

Each blueprint should:

- Have a clear responsibility (e.g., auth, recipes, pantry)
- Implement only related routes
- Use helper functions for validation and logging
- Include docstrings for all public functions

Example blueprint structure:

.. code-block:: python

    from flask import Blueprint, render_template, request, session
    from helpers.validation_helper import validate_input
   
    recipes_bp = Blueprint('recipes', __name__, url_prefix='/recipes')
   
    @recipes_bp.route('/', methods=['GET'])
    def list_recipes():
         """Fetch and display all recipes for the current household"""
         # Implementation
         return render_template('recipes.html', recipes=recipes)

Documentation Standards
~~~~~~~~~~~~~~~~~~~~~~~

Include docstrings for classes, functions, and modules:

.. code-block:: python

    def calculate_daily_nutrition(user_id, date):
         """
         Calculate total nutrition consumed by a user on a given date.
       
         Args:
              user_id (int): The ID of the user
              date (datetime.date): The date to calculate for
           
         Returns:
              dict: Dictionary with 'calories', 'carbs', 'protein', 'fat' keys
           
         Raises:
              ValueError: If user_id is invalid or date is in the future
         """
         # Implementation

Building Documentation
----------------------

The documentation is built using **Sphinx** and deployed via GitHub Pages.

Build Locally
~~~~~~~~~~~~~

.. code-block:: bash

    cd docs
   
    # On Linux/macOS with make:
    make html
   
    # On Windows without make:
      .\make.bat html

The compiled HTML will be in ``docs/_build/html/``. Open ``index.html`` in your browser to preview.

Documentation Structure
~~~~~~~~~~~~~~~~~~~~~~~

- ``introduction.rst`` — Overview and getting started
- ``resources.rst`` — API reference and architecture
- ``troubleshooting.rst`` — Common issues and solutions
- ``development.rst`` — This file; contributor guidelines