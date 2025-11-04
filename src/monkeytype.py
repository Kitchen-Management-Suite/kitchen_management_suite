"""
File: monkeytype.py
Path: src/db/monkeytype.py
Author: ChatGPT ;-;
Date-Created: 10/23/2025

Description:
    Realistic database population script for the Kitchen Management Suite.
    Generates families, friend groups, roommate households with realistic relationships.
    Fetches real recipe data from Fathub and item data from Open Food Facts.
    Tests all database relationships including edge cases.

Usage:
    python src/monkeytype.py
    python src/monkeytype.py --families 15 --friend-groups 8 --roommate-houses 5
"""

import argparse
import random
import datetime
import requests
from bs4 import BeautifulSoup
import tomli
import json

from faker import Faker
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from db.server import get_session, init_database
from db.schema import (
    User, UserProfile, UserNutrition, Role, Household, Member, 
    Pantry, Item, Recipe, Adds, Authors, Holds
)

fake = Faker()
random.seed(2381)  # Deterministic for testing

# Defaults
DEFAULT_FAMILIES = 12
DEFAULT_FRIEND_GROUPS = 6
DEFAULT_ROOMMATE_HOUSES = 4
DEFAULT_SOLO_USERS = 8

# Dietary preferences and allergies pools
DIETARY_PREFS = [
    "vegetarian", "vegan", "pescatarian", "keto", "paleo", 
    "gluten-free", "dairy-free", "low-carb", "mediterranean", None
]

ALLERGIES = [
    "peanuts", "tree nuts", "shellfish", "dairy", "eggs", 
    "soy", "wheat", "fish", None, None, None  # weighted toward no allergies
]

class DataFetcher:
    """Fetches real data from external APIs"""
    
    BASE_TREE_URL = "https://git.sr.ht/~martijnbraam/fathub-data/tree/master/item/en/recipes"
    BASE_BLOB_URL = "https://git.sr.ht/~martijnbraam/fathub-data/blob/master/en/recipes/"

    @staticmethod
    def fetch_fathub_recipes(limit=9999):
        """Fetch all recipes recursively from Fathub TOML blobs"""
        recipes = []
        visited_folders = set()

        def fetch_tree(url, subpath=""):
            """Recursively crawl folders to get all TOML blobs"""
            if subpath in visited_folders:
                return
            visited_folders.add(subpath)

            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # --- Folders ---
                for div in soup.select("div.name.tree > a"):
                    folder_name = div.text.strip()
                    href = div.get("href")

                    # Skip parent folder links or empty
                    if folder_name == ".." or not href:
                        continue

                    # Build subpath
                    new_subpath = f"{subpath}{folder_name}/"
                    # Build tree URL for subfolder
                    tree_url = "https://git.sr.ht" + href
                    fetch_tree(tree_url, new_subpath)

                # --- Files (TOML blobs) ---
                for div in soup.select("div.name.blob > a"):
                    file_name = div.text.strip()
                    if not file_name.endswith(".toml"):
                        continue

                    # Build blob URL
                    blob_url = DataFetcher.BASE_BLOB_URL + subpath + file_name
                    try:
                        blob_resp = requests.get(blob_url, timeout=10)
                        blob_resp.raise_for_status()
                        toml_data = tomli.loads(blob_resp.text)

                        # Flatten instructions
                        instructions = []
                        for block in toml_data.get("instructions", []):
                            instructions.extend(block.get("steps", []))

                        recipe_dict = {
                            "name": toml_data.get("name", "Unnamed Recipe"),
                            "author": toml_data.get("author", None),
                            "created": str(toml_data.get("created", "")),
                            "cuisine": toml_data.get("cuisine", ""),
                            "course": toml_data.get("course", ""),
                            "preptime": toml_data.get("preptime", 0),
                            "cooktime": toml_data.get("cooktime", 0),
                            "serves": toml_data.get("serves", 1),
                            "ingredients": {k: dict(v) for k, v in toml_data.get("ingredients", {}).items()},
                            "instructions": instructions,
                        }

                        recipes.append(recipe_dict)
                        if len(recipes) >= limit:
                            return recipes

                    except Exception as e:
                        print(f"⚠️ Failed to fetch/parse recipe {blob_url}: {e}")

            except Exception as e:
                print(f"⚠️ Failed to fetch tree {url}: {e}")

            return recipes

        return fetch_tree(DataFetcher.BASE_TREE_URL)
    
    @staticmethod
    def fetch_openfoodfacts_items(limit=9999):
        """Fetch real food items from Open Food Facts"""
        try:
            url = f"https://world.openfoodfacts.org/cgi/search.pl?search_simple=1&action=process&json=1&page_size={limit}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = []
                for product in data.get('products', [])[:limit]:
                    name = product.get('product_name', '').strip()
                    if name and len(name) < 100:
                        items.append({
                            'name': name,
                            'brands': product.get('brands', ''),
                            'categories': product.get('categories', ''),
                            'source': 'openfoodfacts'
                        })
                return items
        except Exception as e:
            print(f"⚠️  Could not fetch Open Food Facts items: {e}")
        
        # Fallback common pantry items
        return [
            {'name': 'Milk', 'source': 'custom'},
            {'name': 'Eggs', 'source': 'custom'},
            {'name': 'Bread', 'source': 'custom'},
            {'name': 'Butter', 'source': 'custom'},
            {'name': 'Cheese', 'source': 'custom'},
            {'name': 'Chicken Breast', 'source': 'custom'},
            {'name': 'Ground Beef', 'source': 'custom'},
            {'name': 'Tomatoes', 'source': 'custom'},
            {'name': 'Onions', 'source': 'custom'},
            {'name': 'Garlic', 'source': 'custom'},
            {'name': 'Rice', 'source': 'custom'},
            {'name': 'Pasta', 'source': 'custom'},
            {'name': 'Olive Oil', 'source': 'custom'},
            {'name': 'Salt', 'source': 'custom'},
            {'name': 'Black Pepper', 'source': 'custom'},
        ]


class UserGenerator:
    """Generates realistic users with profiles"""
    
    @staticmethod
    def create_user(first_name=None, last_name=None, age_range=(18, 70)):
        """Create a single user with realistic data"""
        first = first_name or fake.first_name()
        last = last_name or fake.last_name()
        
        # Realistic email patterns
        email_patterns = [
            f"{first.lower()}.{last.lower()}@{fake.free_email_domain()}",
            f"{first.lower()}{last.lower()}@{fake.free_email_domain()}",
            f"{first[0].lower()}{last.lower()}@{fake.free_email_domain()}",
            f"{first.lower()}{random.randint(1, 99)}@{fake.free_email_domain()}",
        ]
        email = random.choice(email_patterns)
        
        # Realistic username patterns
        username = f"{first.lower()}{last.lower()}{random.randint(1, 999)}"
        
        dob = fake.date_of_birth(minimum_age=age_range[0], maximum_age=age_range[1])
        
        user = User(
            FirstName=first,
            LastName=last,
            Username=username,
            Email=email,
            DateOfBirth=dob,
            Password=generate_password_hash("password123")  # In production, this would be properly hashed
        )
        
        return user
    
    @staticmethod
    def create_profile(user, session):
        """Create user profile with realistic health data"""
        age = (datetime.date.today() - user.DateOfBirth).days // 365
        
        # Realistic height/weight based on age
        if age < 25:
            height = random.randint(160, 190)  # cm
            weight = random.randint(55, 90)    # kg
        else:
            height = random.randint(155, 185)
            weight = random.randint(60, 100)
        
        # Calorie goal based on age/weight
        base_calories = 1800 + (weight * 10) + random.randint(-200, 200)
        
        dietary_pref = random.choice(DIETARY_PREFS)
        allergy = random.choice(ALLERGIES)
        
        profile = UserProfile(
            UserID=user.UserID,
            Height=height,
            Weight=weight,
            CalorieGoal=base_calories,
            DietaryPreferences=dietary_pref,
            Allergies=allergy
        )
        
        return profile
    
    @staticmethod
    def create_nutrition_logs(user, days=30):
        """Create realistic nutrition logs for a user"""
        logs = []
        today = datetime.date.today()
        
        for day_offset in range(days):
            date = today - datetime.timedelta(days=day_offset)
            
            # 2-4 meals per day
            num_meals = random.randint(2, 4)
            meal_times = random.sample([
                datetime.time(7, 30),
                datetime.time(12, 0),
                datetime.time(18, 30),
                datetime.time(21, 0)
            ], num_meals)
            
            for meal_time in meal_times:
                calories = random.randint(300, 800)
                protein = random.uniform(10, 40)
                carbs = random.uniform(20, 80)
                fat = random.uniform(5, 35)
                
                log = UserNutrition(
                    UserID=user.UserID,
                    Date=date,
                    Time=meal_time,
                    CaloriesConsumed=calories,
                    Protein=protein,
                    Carbs=carbs,
                    Fat=fat,
                    Fiber=random.uniform(2, 10),
                    Sugar=random.uniform(5, 25),
                    Sodium=random.uniform(200, 1000)
                )
                logs.append(log)
        
        return logs


class HouseholdGenerator:
    """Generates different types of households"""
    
    @staticmethod
    def create_family(session, surname=None):
        """Create a realistic family household"""
        last_name = surname or fake.last_name()
        
        # Parents (2)
        parent1 = UserGenerator.create_user(last_name=last_name, age_range=(35, 55))
        parent2 = UserGenerator.create_user(last_name=last_name, age_range=(35, 55))
        
        # Children (0-4)
        num_children = random.randint(0, 4)
        children = [
            UserGenerator.create_user(last_name=last_name, age_range=(5, 25))
            for _ in range(num_children)
        ]
        
        family_members = [parent1, parent2] + children
        session.add_all(family_members)
        session.flush()
        
        # Create profiles
        for member in family_members:
            profile = UserGenerator.create_profile(member, session)
            session.add(profile)
        
        # Household
        household = Household(HouseholdName=f"{last_name} Family")
        session.add(household)
        session.flush()
        
        # Roles
        owner_role = session.query(Role).filter_by(RoleName="Owner").first()
        member_role = session.query(Role).filter_by(RoleName="Member").first()
        
        # Both parents are owners
        for parent in [parent1, parent2]:
            member = Member(
                UserID=parent.UserID,
                HouseholdID=household.HouseholdID,
                RoleID=owner_role.RoleID
            )
            session.add(member)
        
        # Children are members
        for child in children:
            member = Member(
                UserID=child.UserID,
                HouseholdID=household.HouseholdID,
                RoleID=member_role.RoleID
            )
            session.add(member)
        
        session.commit()
        return household, family_members
    
    @staticmethod
    def create_friend_group(session):
        """Create a friend group household (shared vacation house, etc.)"""
        # 3-6 friends
        num_friends = random.randint(3, 6)
        friends = [UserGenerator.create_user() for _ in range(num_friends)]
        session.add_all(friends)
        session.flush()
        
        for friend in friends:
            profile = UserGenerator.create_profile(friend, session)
            session.add(profile)
        
        # Household named after first friend
        household = Household(HouseholdName=f"{friends[0].FirstName}'s Group")
        session.add(household)
        session.flush()
        
        owner_role = session.query(Role).filter_by(RoleName="Owner").first()
        member_role = session.query(Role).filter_by(RoleName="Member").first()
        
        # First friend is owner, rest are members
        owner_member = Member(
            UserID=friends[0].UserID,
            HouseholdID=household.HouseholdID,
            RoleID=owner_role.RoleID
        )
        session.add(owner_member)
        
        for friend in friends[1:]:
            member = Member(
                UserID=friend.UserID,
                HouseholdID=household.HouseholdID,
                RoleID=member_role.RoleID
            )
            session.add(member)
        
        session.commit()
        return household, friends
    
    @staticmethod
    def create_roommate_house(session):
        """Create a roommate household"""
        num_roommates = random.randint(2, 5)
        roommates = [UserGenerator.create_user(age_range=(22, 35)) for _ in range(num_roommates)]
        session.add_all(roommates)
        session.flush()
        
        for roommate in roommates:
            profile = UserGenerator.create_profile(roommate, session)
            session.add(profile)
        
        household = Household(HouseholdName=f"{fake.street_name()} House")
        session.add(household)
        session.flush()
        
        owner_role = session.query(Role).filter_by(RoleName="Owner").first()
        member_role = session.query(Role).filter_by(RoleName="Member").first()
        
        # All roommates are equal - randomly pick 1-2 owners
        num_owners = random.randint(1, 2)
        owners = random.sample(roommates, num_owners)
        
        for roommate in roommates:
            role = owner_role if roommate in owners else member_role
            member = Member(
                UserID=roommate.UserID,
                HouseholdID=household.HouseholdID,
                RoleID=role.RoleID
            )
            session.add(member)
        
        session.commit()
        return household, roommates


class PantryPopulator:
    """Populates pantries with realistic item distributions"""
    
    @staticmethod
    def create_pantry(session, household):
        """Create pantry for household"""
        pantry = Pantry(
            HouseholdID=household.HouseholdID,
            PantryName=f"{household.HouseholdName} Pantry"
        )
        session.add(pantry)
        session.flush()
        return pantry
    
    @staticmethod
    def add_items_to_pantry(session, pantry, items, household_users):
        """Add items to pantry with realistic user additions"""
        # Each pantry gets 10-30 items
        num_items = random.randint(10, 30)
        selected_items = random.sample(items, min(num_items, len(items)))
        
        adds_records = []
        
        for item in selected_items:
            # 70% chance one user adds, 20% two users, 10% three users
            roll = random.random()
            if roll < 0.7:
                num_adders = 1
            elif roll < 0.9:
                num_adders = 2
            else:
                num_adders = 3
            
            adders = random.sample(household_users, min(num_adders, len(household_users)))
            
            for user in adders:
                quantity = random.randint(1, 10)
                days_ago = random.randint(0, 60)
                date_added = datetime.date.today() - datetime.timedelta(days=days_ago)
                
                add = Adds(
                    UserID=user.UserID,
                    PantryID=pantry.PantryID,
                    ItemID=item.ItemID,
                    Quantity=quantity,
                    ItemInDate=date_added
                )
                adds_records.append(add)
        
        session.add_all(adds_records)
        session.commit()
        return adds_records


class RecipeManager:
    """Manages recipe creation and assignment"""
    
    @staticmethod
    def create_recipes(session, fathub_recipes, all_users):
        """Create global recipes from Fathub and custom recipes"""
        recipes = []
        
        # Add Fathub recipes (global)
        for recipe_data in fathub_recipes:
            recipe = Recipe(
                RecipeName=recipe_data.get('name', 'Unnamed Recipe'),
                RecipeBody=recipe_data,
                Source='fathub',
                IsGlobal=True
            )
            session.add(recipe)
            session.flush()
            recipes.append(recipe)

        # Create custom recipes (15-50)
        num_custom = random.randint(15, 50)
        for _ in range(num_custom):
            recipe = Recipe(
                RecipeName=fake.catch_phrase(),
                RecipeBody={
                    "name": recipe.RecipeName,
                    "author": fake.name(),
                    "created": str(datetime.date.today() - datetime.timedelta(days=random.randint(0, 365))),
                    "cuisine": random.choice(["Italian", "Mexican", "Chinese", "Indian", "American", "Mediterranean", "French", "Japanese"]),
                    "course": random.choice(["appetizer", "main", "dessert", "snack", "beverage"]),
                    "preptime": random.randint(10, 90),
                    "cooktime": random.randint(10, 120),
                    "serves": random.randint(1, 8),
                    "ingredients": {
                        f"ingredient{i}": {
                            "id": fake.word(),
                            "amount": round(random.uniform(0.5, 5.0), 2),
                            "unit": random.choice(["cup", "tablespoon", "teaspoon", "grams", "pieces"])
                        } for i in range(1, random.randint(4, 10))
                    },
                    "instructions": [fake.sentence() for _ in range(random.randint(4, 10))]
                },
                Source='custom',
                IsGlobal=False
            )
            session.add(recipe)
            session.flush()
            recipes.append(recipe)
        
        session.commit()
        return recipes
    
    @staticmethod
    def assign_authors(session, recipes, households):
        """Assign authors to recipes with realistic patterns"""
        authors_records = []
        
        for recipe in recipes:
            # Global recipes: 1-3 random users author across random households
            # Custom recipes: 1-2 users from same household
            
            if recipe.IsGlobal:
                num_household_authors = random.randint(1, 3)
                selected_households = random.sample(households, min(num_household_authors, len(households)))
                
                for household in selected_households:
                    # Get users in this household
                    members = session.query(Member).filter_by(HouseholdID=household.HouseholdID).all()
                    user_ids = [m.UserID for m in members]
                    users = session.query(User).filter(User.UserID.in_(user_ids)).all()
                    
                    author_user = random.choice(users) if users else None
                    if author_user:
                        days_ago = random.randint(0, 365)
                        date_added = datetime.date.today() - datetime.timedelta(days=days_ago)
                        
                        author = Authors(
                            UserID=author_user.UserID,
                            HouseholdID=household.HouseholdID,
                            RecipeID=recipe.RecipeID,
                            DateAdded=date_added,
                            IsCustom=False
                        )
                        authors_records.append(author)
            else:
                # Custom recipe - pick one household
                household = random.choice(households)
                members = session.query(Member).filter_by(HouseholdID=household.HouseholdID).all()
                user_ids = [m.UserID for m in members]
                users = session.query(User).filter(User.UserID.in_(user_ids)).all()
                
                num_authors = random.randint(1, 2)
                selected_users = random.sample(users, min(num_authors, len(users)))
                
                for user in selected_users:
                    days_ago = random.randint(0, 180)
                    date_added = datetime.date.today() - datetime.timedelta(days=days_ago)
                    
                    author = Authors(
                        UserID=user.UserID,
                        HouseholdID=household.HouseholdID,
                        RecipeID=recipe.RecipeID,
                        DateAdded=date_added,
                        IsCustom=True
                    )
                    authors_records.append(author)
        
        session.add_all(authors_records)
        session.commit()
        return authors_records
    
    @staticmethod
    def assign_recipes_to_households(session, recipes, households):
        """Assign recipes to households (Holds relationship)"""
        holds_records = []
        
        for household in households:
            # Each household holds 5-20 recipes
            num_recipes = random.randint(5, 20)
            selected_recipes = random.sample(recipes, min(num_recipes, len(recipes)))
            
            for recipe in selected_recipes:
                hold = Holds(
                    HouseholdID=household.HouseholdID,
                    RecipeID=recipe.RecipeID
                )
                holds_records.append(hold)
        
        session.add_all(holds_records)
        session.commit()
        return holds_records

def ensure_roles(session):
    """Ensure basic roles exist"""
    role_names = ["Owner", "Admin", "Member", "Viewer"]
    existing_roles = {r.RoleName: r for r in session.query(Role).all()}
    
    for role_name in role_names:
        if role_name not in existing_roles:
            role = Role(RoleName=role_name)
            session.add(role)
    
    session.commit()
    return session.query(Role).all()


def create_cross_household_edge_cases(session, all_users, households, items):
    """Create edge cases: users in multiple households, same item in multiple pantries"""
    
    # Edge case 1: Some users belong to multiple households (10% of users)
    multi_household_users = random.sample(all_users, max(1, len(all_users) // 10))
    member_role = session.query(Role).filter_by(RoleName="Member").first()
    
    for user in multi_household_users:
        # Add them to 1-2 additional households
        num_additional = random.randint(1, 2)
        # Get households they're NOT already in
        current_households = session.query(Member).filter_by(UserID=user.UserID).all()
        current_household_ids = {m.HouseholdID for m in current_households}
        available_households = [h for h in households if h.HouseholdID not in current_household_ids]
        
        if available_households:
            additional_households = random.sample(
                available_households, 
                min(num_additional, len(available_households))
            )
            
            for household in additional_households:
                member = Member(
                    UserID=user.UserID,
                    HouseholdID=household.HouseholdID,
                    RoleID=member_role.RoleID
                )
                session.add(member)
    
    # Edge case 2: Same item added by same user to different households
    for user in random.sample(multi_household_users, min(5, len(multi_household_users))):
        user_households = session.query(Member).filter_by(UserID=user.UserID).all()
        if len(user_households) >= 2:
            item = random.choice(items)
            
            for member in user_households[:2]:  # Add to first 2 households
                household = session.query(Household).get(member.HouseholdID)
                pantry = household.pantry
                
                if pantry:
                    add = Adds(
                        UserID=user.UserID,
                        PantryID=pantry.PantryID,
                        ItemID=item.ItemID,
                        Quantity=random.randint(1, 5),
                        ItemInDate=datetime.date.today()
                    )
                    session.add(add)
    
    session.commit()
    print("✅ Created cross-household edge cases")


def populate_database(num_families, num_friend_groups, num_roommate_houses, num_solo_users):
    """Main population function"""
    
    print("🔧 Initializing database...")
    init_database()
    session = get_session()
    
    try:
        print("📋 Ensuring roles exist...")
        ensure_roles(session)
        
        print("🌐 Fetching external data...")
        fetcher = DataFetcher()
        fathub_recipes = fetcher.fetch_fathub_recipes(limit=30)
        openfoodfacts_items = fetcher.fetch_openfoodfacts_items(limit=80)
        
        print(f"   Fetched {len(fathub_recipes)} recipes and {len(openfoodfacts_items)} items")
        
        # Create items
        print("🥫 Creating items...")
        items = []
        for item_data in openfoodfacts_items:
            item = Item(
                ItemName=item_data['name'],
                ItemBody=json.dumps(item_data),
                Source=item_data.get('source', 'openfoodfacts'),
                IsGlobal=item_data.get('source') == 'openfoodfacts'
            )
            items.append(item)
        
        session.add_all(items)
        session.commit()
        
        # Create households
        print("🏠 Creating families...")
        all_users = []
        households = []
        
        for i in range(num_families):
            household, members = HouseholdGenerator.create_family(session)
            households.append(household)
            all_users.extend(members)
            print(f"   Family {i+1}/{num_families}: {household.HouseholdName} ({len(members)} members)")
        
        print("👥 Creating friend groups...")
        for i in range(num_friend_groups):
            household, members = HouseholdGenerator.create_friend_group(session)
            households.append(household)
            all_users.extend(members)
            print(f"   Friend group {i+1}/{num_friend_groups}: {household.HouseholdName}")
        
        print("🏘️  Creating roommate houses...")
        for i in range(num_roommate_houses):
            household, members = HouseholdGenerator.create_roommate_house(session)
            households.append(household)
            all_users.extend(members)
            print(f"   Roommate house {i+1}/{num_roommate_houses}: {household.HouseholdName}")
        
        print("🧍 Creating solo users...")
        for i in range(num_solo_users):
            user = UserGenerator.create_user()
            session.add(user)
            session.flush()
            profile = UserGenerator.create_profile(user, session)
            session.add(profile)
            all_users.append(user)
        session.commit()
        
        # Create pantries
        print("🗄️  Creating pantries...")
        for household in households:
            pantry = PantryPopulator.create_pantry(session, household)
            
            # Get household users
            members = session.query(Member).filter_by(HouseholdID=household.HouseholdID).all()
            user_ids = [m.UserID for m in members]
            household_users = session.query(User).filter(User.UserID.in_(user_ids)).all()
            
            # Add items to pantry
            PantryPopulator.add_items_to_pantry(session, pantry, items, household_users)
        
        print("📖 Creating recipes...")
        recipes = RecipeManager.create_recipes(session, fathub_recipes, all_users)
        
        print("✍️  Assigning recipe authors...")
        RecipeManager.assign_authors(session, recipes, households)
        
        print("📚 Assigning recipes to households...")
        RecipeManager.assign_recipes_to_households(session, recipes, households)
        
        print("📊 Creating nutrition logs...")
        for user in random.sample(all_users, min(len(all_users) // 2, 50)):
            logs = UserGenerator.create_nutrition_logs(user, days=random.randint(7, 30))
            session.add_all(logs)
        session.commit()
        
        print("🔀 Creating edge cases...")
        create_cross_household_edge_cases(session, all_users, households, items)
        
        # Print summary
        print("\n" + "="*50)
        print("📊 DATABASE POPULATION SUMMARY")
        print("="*50)
        print(f"Users:              {session.query(User).count()}")
        print(f"User Profiles:      {session.query(UserProfile).count()}")
        print(f"Nutrition Logs:     {session.query(UserNutrition).count()}")
        print(f"Households:         {session.query(Household).count()}")
        print(f"  - Families:       {num_families}")
        print(f"  - Friend Groups:  {num_friend_groups}")
        print(f"  - Roommate Houses: {num_roommate_houses}")
        print(f"Members:            {session.query(Member).count()}")
        print(f"Pantries:           {session.query(Pantry).count()}")
        print(f"Items:              {session.query(Item).count()}")
        print(f"Recipes:            {session.query(Recipe).count()}")
        print(f"  - Global:         {session.query(Recipe).filter_by(IsGlobal=True).count()}")
        print(f"  - Custom:         {session.query(Recipe).filter_by(IsGlobal=False).count()}")
        print(f"Authors:            {session.query(Authors).count()}")
        print(f"Adds:               {session.query(Adds).count()}")
        print(f"Holds:              {session.query(Holds).count()}")
        print("="*50)
        print("✅ Database population complete!")
        
    except IntegrityError as e:
        session.rollback()
        print(f"❌ Integrity error: {e}")
        raise
    except Exception as e:
        session.rollback()
        print(f"❌ Error populating database: {e}")
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Populate database with realistic test data (monkeytype approach)"
    )
    parser.add_argument("--families", type=int, default=DEFAULT_FAMILIES,
                       help=f"Number of family households (default: {DEFAULT_FAMILIES})")
    parser.add_argument("--friend-groups", type=int, default=DEFAULT_FRIEND_GROUPS,
                       help=f"Number of friend group households (default: {DEFAULT_FRIEND_GROUPS})")
    parser.add_argument("--roommate-houses", type=int, default=DEFAULT_ROOMMATE_HOUSES,
                       help=f"Number of roommate households (default: {DEFAULT_ROOMMATE_HOUSES})")
    parser.add_argument("--solo-users", type=int, default=DEFAULT_SOLO_USERS,
                       help=f"Number of solo users (default: {DEFAULT_SOLO_USERS})")
    
    args = parser.parse_args()
    
    print("🐵 MONKEYTYPE DATABASE POPULATOR 🐵")
    print("Infinite monkeys with typewriters, but for databases!\n")
    
    populate_database(
        num_families=args.families,
        num_friend_groups=args.friend_groups,
        num_roommate_houses=args.roommate_houses,
        num_solo_users=args.solo_users
    )


if __name__ == "__main__":
    main()