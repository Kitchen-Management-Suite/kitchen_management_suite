"""
File: unit_converter.py
File-Path: src/helpers/unit_converter.py
Author: Claude
Date-Created: 12-04-2025

Description:
    Comprehensive unit conversion system for ingredient measurements.
    Handles weight, volume, and specialized units with proper conversions.

Inputs:
    Amounts and units from recipes and pantry items

Outputs:
    Normalized quantities for comparison and calculation
"""


class UnitConverter:
    """
    Comprehensive unit conversion system.
    All conversions normalize to grams for weight and milliliters for volume.
    """

    # Weight conversions to grams
    WEIGHT_TO_GRAMS = {
        # Metric
        'g': 1,
        'gram': 1,
        'grams': 1,
        'kg': 1000,
        'kilogram': 1000,
        'kilograms': 1000,
        'mg': 0.001,
        'milligram': 0.001,
        'milligrams': 0.001,

        # Imperial
        'oz': 28.3495,
        'ounce': 28.3495,
        'ounces': 28.3495,
        'lb': 453.592,
        'lbs': 453.592,
        'pound': 453.592,
        'pounds': 453.592,
    }

    # Volume conversions to milliliters
    VOLUME_TO_ML = {
        # Metric
        'ml': 1,
        'milliliter': 1,
        'milliliters': 1,
        'l': 1000,
        'liter': 1000,
        'liters': 1000,
        'dl': 100,
        'deciliter': 100,
        'deciliters': 100,

        # US Imperial
        'cup': 236.588,
        'cups': 236.588,
        'tbsp': 14.7868,
        'tablespoon': 14.7868,
        'tablespoons': 14.7868,
        'tsp': 4.92892,
        'teaspoon': 4.92892,
        'teaspoons': 4.92892,
        'fl oz': 29.5735,
        'fluid ounce': 29.5735,
        'fluid ounces': 29.5735,
        'pt': 473.176,
        'pint': 473.176,
        'pints': 473.176,
        'qt': 946.353,
        'quart': 946.353,
        'quarts': 946.353,
        'gal': 3785.41,
        'gallon': 3785.41,
        'gallons': 3785.41,
    }

    # Specialized food item conversions (approximate weights in grams)
    SPECIALIZED_UNITS = {
        # Butter/Margarine
        'stick': {'grams': 113.4, 'cups': 0.5, 'tbsp': 8},
        'sticks': {'grams': 113.4, 'cups': 0.5, 'tbsp': 8},
        'stick of butter': {'grams': 113.4},
        'pat': {'grams': 5},  # butter pat
        'pats': {'grams': 5},

        # Eggs
        'egg': {'grams': 50},
        'eggs': {'grams': 50},
        'large egg': {'grams': 50},
        'medium egg': {'grams': 44},
        'small egg': {'grams': 38},
        'egg white': {'grams': 33},
        'egg yolk': {'grams': 17},

        # Produce
        'clove': {'grams': 3},  # garlic clove
        'cloves': {'grams': 3},
        'head': {'grams': 40},  # garlic head
        'heads': {'grams': 40},
        'bunch': {'grams': 100},  # herbs/greens
        'bunches': {'grams': 100},
        'sprig': {'grams': 5},
        'sprigs': {'grams': 5},
        'leaf': {'grams': 5},
        'leaves': {'grams': 5},

        # Misc
        'slice': {'grams': 28},  # bread slice
        'slices': {'grams': 28},
        'piece': {'grams': 100},  # generic piece
        'pieces': {'grams': 100},
        'whole': {'grams': 150},  # generic whole item
        'can': {'ml': 354},  # standard can (12 oz)
        'cans': {'ml': 354},
        'package': {'grams': 200},  # generic package
        'packages': {'grams': 200},
        'box': {'grams': 400},  # generic box
        'boxes': {'grams': 400},

        # Special cases
        'pinch': {'grams': 0.5},
        'pinches': {'grams': 0.5},
        'dash': {'grams': 0.6},
        'dashes': {'grams': 0.6},
        'to taste': {'grams': 5},  # Arbitrary small amount
        '': {'grams': 100},  # Default for no unit
    }

    # Ingredient-specific density factors (grams per cup)
    INGREDIENT_DENSITIES = {
        # Flours
        'flour': 120,
        'all-purpose flour': 120,
        'bread flour': 127,
        'cake flour': 114,
        'whole wheat flour': 120,
        'almond flour': 96,

        # Sugars
        'sugar': 200,
        'granulated sugar': 200,
        'brown sugar': 220,
        'powdered sugar': 120,
        'confectioners sugar': 120,
        'icing sugar': 120,

        # Fats
        'butter': 227,
        'margarine': 227,
        'oil': 218,
        'vegetable oil': 218,
        'olive oil': 216,
        'coconut oil': 218,
        'shortening': 191,

        # Dairy
        'milk': 245,
        'cream': 240,
        'heavy cream': 240,
        'sour cream': 230,
        'yogurt': 245,
        'cheese': 113,  # shredded

        # Grains & Pasta
        'rice': 185,
        'pasta': 100,
        'oats': 80,
        'quinoa': 170,

        # Nuts & Seeds
        'almonds': 143,
        'walnuts': 117,
        'pecans': 99,
        'peanuts': 146,

        # Liquids (most are close to water)
        'water': 237,
        'broth': 240,
        'stock': 240,
        'juice': 240,

        # Misc
        'cocoa powder': 85,
        'honey': 340,
        'maple syrup': 315,
        'peanut butter': 258,
        'jam': 320,
    }

    @classmethod
    def normalize_unit(cls, unit_str):
        """Normalize unit string to lowercase and remove extra spaces."""
        if not unit_str:
            return ''
        return unit_str.lower().strip()

    @classmethod
    def convert_to_base_unit(cls, amount, unit, ingredient_name=None):
        """
        Convert any unit to a base unit (grams or ml).

        Args:
            amount: Numeric amount
            unit: Unit string
            ingredient_name: Optional ingredient name for density-based conversions

        Returns:
            tuple: (converted_amount, base_unit) where base_unit is 'g' or 'ml'
        """
        if amount <= 0:
            return (0, 'g')

        unit = cls.normalize_unit(unit)

        # Check weight units first
        if unit in cls.WEIGHT_TO_GRAMS:
            return (amount * cls.WEIGHT_TO_GRAMS[unit], 'g')

        # Check volume units
        if unit in cls.VOLUME_TO_ML:
            ml = amount * cls.VOLUME_TO_ML[unit]

            # If we have ingredient name, try to convert volume to weight
            if ingredient_name:
                ingredient_name = cls.normalize_unit(ingredient_name)

                # Check for specific ingredient density
                for ing_key, density_per_cup in cls.INGREDIENT_DENSITIES.items():
                    if ing_key in ingredient_name or ingredient_name in ing_key:
                        # Convert ml to cups, then cups to grams using density
                        cups = ml / 236.588
                        grams = cups * density_per_cup
                        return (grams, 'g')

            return (ml, 'ml')

        # Check specialized units
        if unit in cls.SPECIALIZED_UNITS:
            spec = cls.SPECIALIZED_UNITS[unit]
            if 'grams' in spec:
                return (amount * spec['grams'], 'g')
            elif 'ml' in spec:
                return (amount * spec['ml'], 'ml')

        # Default: treat as generic piece (100g)
        return (amount * 100, 'g')

    @classmethod
    def can_convert_between(cls, unit1, unit2):
        """Check if two units can be meaningfully compared."""
        unit1 = cls.normalize_unit(unit1)
        unit2 = cls.normalize_unit(unit2)

        # Get base units for both
        _, base1 = cls.convert_to_base_unit(1, unit1)
        _, base2 = cls.convert_to_base_unit(1, unit2)

        # Can only compare if both normalize to same base unit
        return base1 == base2

    @classmethod
    def compare_quantities(cls, amount1, unit1, amount2, unit2, ingredient_name=None):
        """
        Compare two quantities and return if amount1 >= amount2.

        Returns:
            tuple: (comparison_result: bool, amount1_in_base, amount2_in_base, base_unit)
        """
        # Convert both to base units
        base_amount1, base_unit1 = cls.convert_to_base_unit(amount1, unit1, ingredient_name)
        base_amount2, base_unit2 = cls.convert_to_base_unit(amount2, unit2, ingredient_name)

        # If units don't match, can't reliably compare
        if base_unit1 != base_unit2:
            return (False, base_amount1, base_amount2, base_unit1)

        return (base_amount1 >= base_amount2, base_amount1, base_amount2, base_unit1)
