"""
Unit tests for scoring functions.
"""

import pytest
from src.agents.food_compatibility_agent import calculate_food_scores
from src.agents.cosmetics_compatibility_agent import calculate_cosmetics_scores
from src.agents.household_compatibility_agent import calculate_household_scores


class TestFoodScoring:
    """Tests for food product scoring."""
    
    def test_strict_allergen_explicit_zero_safety(self, sample_food_profile):
        """Strict allergen in ingredients should result in safety_score = 0."""
        ingredients = ["water", "hazelnut", "sugar", "cocoa"]
        ingredient_risks = {
            "hazelnut": ["allergen"],
            "sugar": ["high_sugar"],
        }
        
        result = calculate_food_scores(
            profile=sample_food_profile,
            ingredient_risks=ingredient_risks,
            ingredients_list=ingredients,
        )
        
        assert result["status"] == "success"
        assert result["safety_score"] == 0
        assert result["final_cap"] <= 15
        assert result["has_strict_allergen_explicit"] is True
        assert len(result["safety_issues"]) > 0
    
    def test_strict_allergen_traces_lowers_safety(self, sample_food_profile):
        """Strict allergen in traces should lower safety but not to zero."""
        ingredients = ["water", "may contain traces of hazelnut", "sugar"]
        ingredient_risks = {
            "hazelnut": ["allergen"],
        }
        
        result = calculate_food_scores(
            profile=sample_food_profile,
            ingredient_risks=ingredient_risks,
            ingredients_list=ingredients,
        )
        
        assert result["status"] == "success"
        assert result["safety_score"] < 100
        assert result["safety_score"] >= 20  # Traces penalty
        assert result["has_strict_allergen_traces"] is True
    
    def test_prefer_avoid_affects_sensitivity(self, sample_food_profile):
        """Prefer_avoid ingredients should affect sensitivity_score, not safety."""
        ingredients = ["water", "sugar", "cocoa"]
        ingredient_risks = {
            "sugar": ["high_sugar"],
        }
        
        result = calculate_food_scores(
            profile=sample_food_profile,
            ingredient_risks=ingredient_risks,
            ingredients_list=ingredients,
        )
        
        assert result["status"] == "success"
        assert result["safety_score"] == 100  # Safety not affected
        assert result["sensitivity_score"] < 100  # Sensitivity affected
        assert len(result["sensitivity_issues"]) > 0
    
    def test_no_issues_high_scores(self, sample_food_profile):
        """Product with no issues should have high scores."""
        ingredients = ["water", "cocoa", "vanilla"]
        ingredient_risks = {}
        
        result = calculate_food_scores(
            profile=sample_food_profile,
            ingredient_risks=ingredient_risks,
            ingredients_list=ingredients,
        )
        
        assert result["status"] == "success"
        assert result["safety_score"] == 100
        assert result["sensitivity_score"] >= 90
        assert result["for_me_score"] >= 80
    
    def test_risk_tags_affect_sensitivity(self, sample_food_profile):
        """Risk tags (high_salt, high_sugar) should affect sensitivity."""
        ingredients = ["water", "salt", "sugar"]
        ingredient_risks = {
            "salt": ["high_salt"],
            "sugar": ["high_sugar"],
        }
        
        result = calculate_food_scores(
            profile=sample_food_profile,
            ingredient_risks=ingredient_risks,
            ingredients_list=ingredients,
        )
        
        assert result["status"] == "success"
        assert result["sensitivity_score"] < 100
        assert len(result["sensitivity_issues"]) > 0


class TestCosmeticsScoring:
    """Tests for cosmetics product scoring."""
    
    def test_strict_avoid_lowers_safety(self, sample_cosmetics_profile):
        """Strict_avoid in cosmetics should lower safety."""
        profile = sample_cosmetics_profile.copy()
        profile["strict_avoid"] = [{"ingredient": "sodium lauryl sulfate", "type": "allergen"}]
        
        ingredients = ["water", "sodium lauryl sulfate", "glycerin"]
        ingredient_risks = {
            "sodium lauryl sulfate": ["harsh_surfactant"],
        }
        
        result = calculate_cosmetics_scores(
            profile=profile,
            ingredient_risks=ingredient_risks,
            ingredients_list=ingredients,
        )
        
        assert result["status"] == "success"
        assert result["safety_score"] < 100
        assert len(result["safety_issues"]) > 0
    
    def test_sensitivities_affect_sensitivity_score(self, sample_cosmetics_profile):
        """Cosmetics sensitivities should affect sensitivity_score, not safety."""
        ingredients = ["water", "fragrance", "glycerin"]
        ingredient_risks = {
            "fragrance": ["fragrance", "irritant"],
        }
        
        result = calculate_cosmetics_scores(
            profile=sample_cosmetics_profile,
            ingredient_risks=ingredient_risks,
            ingredients_list=ingredients,
        )
        
        assert result["status"] == "success"
        assert result["safety_score"] == 100  # Safety not affected
        assert result["sensitivity_score"] < 100  # Sensitivity affected
        assert len(result["sensitivity_issues"]) > 0
    
    def test_hair_goals_affect_match(self, sample_cosmetics_profile):
        """Hair goals should affect match_score."""
        ingredients = ["water", "glycerin", "hyaluronic acid"]
        ingredient_risks = {
            "glycerin": ["hydrating"],
            "hyaluronic acid": ["hydrating"],
        }
        
        result = calculate_cosmetics_scores(
            profile=sample_cosmetics_profile,
            ingredient_risks=ingredient_risks,
            ingredients_list=ingredients,
        )
        
        assert result["status"] == "success"
        assert result["match_score"] > 50  # Should be boosted by hydration goal
    
    def test_no_issues_high_scores(self, sample_cosmetics_profile):
        """Product with no issues should have high scores."""
        ingredients = ["water", "glycerin", "dimethicone"]
        ingredient_risks = {}
        
        result = calculate_cosmetics_scores(
            profile=sample_cosmetics_profile,
            ingredient_risks=ingredient_risks,
            ingredients_list=ingredients,
        )
        
        assert result["status"] == "success"
        assert result["safety_score"] == 100
        assert result["sensitivity_score"] >= 90
        assert result["for_me_score"] >= 80


class TestHouseholdScoring:
    """Tests for household product scoring."""
    
    def test_strict_avoid_lowers_safety(self):
        """Strict_avoid in household should lower safety."""
        profile = {
            "household_strict_avoid": ["sodium hypochlorite", "bleach"],
            "household_sensitivities": [],
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
        
        ingredients = ["water", "sodium hypochlorite", "surfactant"]
        ingredient_risks = {
            "sodium hypochlorite": ["bleach", "chlorine"],
        }
        
        result = calculate_household_scores(
            profile=profile,
            ingredient_risks=ingredient_risks,
            ingredients_list=ingredients,
        )
        
        assert result["status"] == "success"
        assert result["safety_score"] < 100
        # Household agent returns risk_analysis, not safety_issues
        assert "risk_analysis" in result or "safety_issues" in result
    
    def test_sensitivities_affect_sensitivity(self):
        """Household sensitivities should affect sensitivity_score."""
        profile = {
            "household_strict_avoid": [],
            "household_sensitivities": ["ammonia", "strong_solvents"],
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
        
        ingredients = ["water", "ammonia", "surfactant"]
        ingredient_risks = {
            "ammonia": ["irritant"],
        }
        
        result = calculate_household_scores(
            profile=profile,
            ingredient_risks=ingredient_risks,
            ingredients_list=ingredients,
        )
        
        assert result["status"] == "success"
        assert result["sensitivity_score"] < 100
        # Household agent may not return sensitivity_issues, check risk_analysis instead
        assert "risk_analysis" in result or "sensitivity_issues" in result
    
    def test_no_issues_high_scores(self):
        """Product with no issues should have high scores."""
        profile = {
            "household_strict_avoid": [],
            "household_sensitivities": [],
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
        
        ingredients = ["water", "surfactant", "glycerin"]
        ingredient_risks = {}
        
        result = calculate_household_scores(
            profile=profile,
            ingredient_risks=ingredient_risks,
            ingredients_list=ingredients,
        )
        
        assert result["status"] == "success"
        assert result["safety_score"] == 100
        assert result["sensitivity_score"] >= 90
        assert result["for_me_score"] >= 80

