"""
Scoring weight constants for FOR ME Score calculation.

These weights determine how Safety, Sensitivity, and Match scores
are combined into the final FOR ME Score for each product category.
"""

# Food scoring weights (Safety is most important)
FOOD_SAFETY_WEIGHT = 0.5
FOOD_SENSITIVITY_WEIGHT = 0.3
FOOD_MATCH_WEIGHT = 0.2

# Cosmetics scoring weights (Match is more important)
COSMETICS_SAFETY_WEIGHT = 0.3
COSMETICS_SENSITIVITY_WEIGHT = 0.3
COSMETICS_MATCH_WEIGHT = 0.4

# Household scoring weights (balanced)
HOUSEHOLD_SAFETY_WEIGHT = 0.4
HOUSEHOLD_SENSITIVITY_WEIGHT = 0.3
HOUSEHOLD_MATCH_WEIGHT = 0.3

# General scoring weights (default)
DEFAULT_SAFETY_WEIGHT = 0.4
DEFAULT_SENSITIVITY_WEIGHT = 0.3
DEFAULT_MATCH_WEIGHT = 0.3

