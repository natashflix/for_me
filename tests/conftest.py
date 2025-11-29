"""
Pytest configuration and fixtures for FOR ME tests.
"""

import pytest
from typing import Dict, Any
from copy import deepcopy
from src.memory import DEFAULT_EMPTY_PROFILE


@pytest.fixture
def empty_profile() -> Dict[str, Any]:
    """Returns an empty user profile."""
    return deepcopy(DEFAULT_EMPTY_PROFILE)


@pytest.fixture
def sample_food_profile() -> Dict[str, Any]:
    """Returns a sample food profile with allergies and preferences."""
    return {
        "food_strict_avoid": [
            {"ingredient": "hazelnut", "type": "allergen"},
            {"ingredient": "peanut", "type": "allergen"},
        ],
        "food_prefer_avoid": [
            {"ingredient": "sugar", "type": "preference"},
            {"ingredient": "high_salt", "type": "preference"},
        ],
        "food_ok_if_small": [
            {"ingredient": "soy", "type": "preference"},
        ],
        "repeated_negative_reactions": [],
        "hair_type": None,
        "hair_goals": [],
        "skin_type": None,
        "skin_goals": [],
        "cosmetics_sensitivities": [],
        "cosmetics_preferences": [],
        "household_strict_avoid": [],
        "household_sensitivities": [],
    }


@pytest.fixture
def sample_cosmetics_profile() -> Dict[str, Any]:
    """Returns a sample cosmetics profile with sensitivities."""
    return {
        "cosmetics_sensitivities": ["fragrance", "SLS", "drying_alcohol"],
        "cosmetics_preferences": ["silicone_free"],
        "hair_type": "curly",
        "hair_goals": ["hydration", "anti_frizz"],
        "skin_type": "sensitive",
        "skin_goals": ["hydration", "reduce_irritation"],
        "food_strict_avoid": [],
        "food_prefer_avoid": [],
        "food_ok_if_small": [],
        "repeated_negative_reactions": [],
        "household_strict_avoid": [],
        "household_sensitivities": [],
    }


@pytest.fixture
def sample_ingredient_risks() -> Dict[str, list]:
    """Returns sample ingredient risk mappings."""
    return {
        "sodium lauryl sulfate": ["harsh_surfactant", "irritant"],
        "fragrance": ["fragrance", "irritant"],
        "parabens": ["preservative", "controversial"],
        "sugar": ["high_sugar"],
        "salt": ["high_salt"],
        "gluten": ["allergen"],
    }


@pytest.fixture
def sample_ingredients_list() -> list:
    """Returns a sample normalized ingredients list."""
    return [
        "water",
        "sodium lauryl sulfate",
        "glycerin",
        "fragrance",
        "cocoa butter",
    ]


@pytest.fixture
def mock_tool_context():
    """Returns a mock ToolContext object."""
    class MockToolContext:
        def __init__(self):
            self.state = {}
    
    return MockToolContext()

