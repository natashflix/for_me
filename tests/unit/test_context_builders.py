"""
Unit tests for context builder functions.
"""

import pytest
from src.agents.food_compatibility_agent import build_food_context
from src.agents.cosmetics_compatibility_agent import build_cosmetics_context
from src.agents.household_compatibility_agent import build_household_context


class TestFoodContextBuilder:
    """Tests for build_food_context function."""
    
    def test_builds_structured_context(self, sample_food_profile, sample_ingredients_list, sample_ingredient_risks):
        """Should build structured context with all required fields."""
        context = build_food_context(
            profile=sample_food_profile,
            ingredients_list=sample_ingredients_list,
            ingredient_risks=sample_ingredient_risks,
        )
        
        assert "profile" in context
        assert "ingredients" in context
        assert "ingredient_risks" in context
        assert "dictionaries" in context
    
    def test_profile_data_in_context(self, sample_food_profile, sample_ingredients_list, sample_ingredient_risks):
        """Should include profile data in context."""
        context = build_food_context(
            profile=sample_food_profile,
            ingredients_list=sample_ingredients_list,
            ingredient_risks=sample_ingredient_risks,
        )
        
        assert "food_strict_avoid" in context["profile"]
        assert "food_prefer_avoid" in context["profile"]
        assert context["profile"]["food_strict_avoid"] == sample_food_profile["food_strict_avoid"]
    
    def test_ingredients_in_context(self, sample_food_profile, sample_ingredients_list, sample_ingredient_risks):
        """Should include ingredients list in context."""
        context = build_food_context(
            profile=sample_food_profile,
            ingredients_list=sample_ingredients_list,
            ingredient_risks=sample_ingredient_risks,
        )
        
        assert context["ingredients"] == sample_ingredients_list
    
    def test_risks_in_context(self, sample_food_profile, sample_ingredients_list, sample_ingredient_risks):
        """Should include risk mappings in context."""
        context = build_food_context(
            profile=sample_food_profile,
            ingredients_list=sample_ingredients_list,
            ingredient_risks=sample_ingredient_risks,
        )
        
        assert context["ingredient_risks"] == sample_ingredient_risks


class TestCosmeticsContextBuilder:
    """Tests for build_cosmetics_context function."""
    
    def test_builds_structured_context(self, sample_cosmetics_profile, sample_ingredients_list, sample_ingredient_risks):
        """Should build structured context with all required fields."""
        context = build_cosmetics_context(
            profile=sample_cosmetics_profile,
            ingredients_list=sample_ingredients_list,
            ingredient_risks=sample_ingredient_risks,
        )
        
        assert "profile" in context
        assert "ingredients" in context
        assert "ingredient_risks" in context
    
    def test_cosmetics_profile_data_in_context(self, sample_cosmetics_profile, sample_ingredients_list, sample_ingredient_risks):
        """Should include cosmetics-specific profile data."""
        context = build_cosmetics_context(
            profile=sample_cosmetics_profile,
            ingredients_list=sample_ingredients_list,
            ingredient_risks=sample_ingredient_risks,
        )
        
        assert "cosmetics_sensitivities" in context["profile"]
        assert "hair_type" in context["profile"]
        assert "hair_goals" in context["profile"]
        assert context["profile"]["hair_type"] == sample_cosmetics_profile["hair_type"]


class TestHouseholdContextBuilder:
    """Tests for build_household_context function."""
    
    def test_builds_structured_context(self):
        """Should build structured context for household products."""
        profile = {
            "household_strict_avoid": ["bleach"],
            "household_sensitivities": ["ammonia"],
            "food_strict_avoid": [],
            "food_prefer_avoid": [],
            "food_ok_if_small": [],
            "cosmetics_sensitivities": [],
            "cosmetics_preferences": [],
            "repeated_negative_reactions": [],
            "hair_type": None,
            "hair_goals": [],
            "skin_type": None,
            "skin_goals": [],
        }
        ingredients = ["water", "sodium hypochlorite"]
        risks = {"sodium hypochlorite": ["bleach"]}
        
        context = build_household_context(
            profile=profile,
            ingredients_list=ingredients,
            ingredient_risks=risks,
        )
        
        assert "profile" in context
        assert "ingredients" in context
        assert "ingredient_risks" in context
        assert "household_strict_avoid" in context["profile"]

