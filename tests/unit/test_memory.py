"""
Unit tests for memory functions.
"""

import pytest
from src.memory import (
    is_profile_minimal,
    apply_repeated_reactions_to_scores,
    _ensure_list,
    DEFAULT_EMPTY_PROFILE,
)


class TestIsProfileMinimal:
    """Tests for is_profile_minimal function."""
    
    def test_empty_profile_is_minimal(self, empty_profile):
        """Empty profile should be considered minimal."""
        assert is_profile_minimal(empty_profile) is True
    
    def test_none_profile_is_minimal(self):
        """None profile should be considered minimal."""
        assert is_profile_minimal(None) is True
    
    def test_profile_with_food_strict_avoid_not_minimal(self, empty_profile):
        """Profile with food_strict_avoid should not be minimal."""
        profile = empty_profile.copy()
        profile["food_strict_avoid"] = [{"ingredient": "peanut", "type": "allergen"}]
        assert is_profile_minimal(profile) is False
    
    def test_profile_with_hair_type_not_minimal(self, empty_profile):
        """Profile with hair_type should not be minimal."""
        profile = empty_profile.copy()
        profile["hair_type"] = "curly"
        assert is_profile_minimal(profile) is False
    
    def test_profile_with_hair_goals_not_minimal(self, empty_profile):
        """Profile with hair_goals should not be minimal."""
        profile = empty_profile.copy()
        profile["hair_goals"] = ["hydration"]
        assert is_profile_minimal(profile) is False
    
    def test_profile_with_skin_goals_not_minimal(self, empty_profile):
        """Profile with skin_goals should not be minimal."""
        profile = empty_profile.copy()
        profile["skin_goals"] = ["hydration"]
        assert is_profile_minimal(profile) is False
    
    def test_profile_with_repeated_reactions_not_minimal(self, empty_profile):
        """Profile with repeated_negative_reactions should not be minimal."""
        profile = empty_profile.copy()
        profile["repeated_negative_reactions"] = [
            {"ingredient": "SLS", "reaction": "itching", "frequency": "always"}
        ]
        assert is_profile_minimal(profile) is False


class TestApplyRepeatedReactionsToScores:
    """Tests for apply_repeated_reactions_to_scores function."""
    
    def test_no_reactions_no_change(self, empty_profile):
        """No repeated reactions should not change scores."""
        safety_score = 100
        final_cap = 100
        ingredients = ["water", "glycerin"]
        
        new_safety, new_cap = apply_repeated_reactions_to_scores(
            profile=empty_profile,
            ingredients_list=ingredients,
            current_safety_score=safety_score,
            current_final_cap=final_cap,
        )
        
        assert new_safety == safety_score
        assert new_cap == final_cap
    
    def test_severe_reaction_lowers_safety(self, empty_profile):
        """Severe reaction (always) should lower safety score."""
        profile = empty_profile.copy()
        profile["repeated_negative_reactions"] = [
            {
                "ingredient": "sodium lauryl sulfate",
                "reaction": "itching",
                "frequency": "always",
            }
        ]
        
        safety_score = 100
        final_cap = 100
        ingredients = ["water", "sodium lauryl sulfate", "glycerin"]
        
        new_safety, new_cap = apply_repeated_reactions_to_scores(
            profile=profile,
            ingredients_list=ingredients,
            current_safety_score=safety_score,
            current_final_cap=final_cap,
        )
        
        assert new_safety < safety_score
        assert new_cap < final_cap
    
    def test_moderate_reaction_moderate_penalty(self, empty_profile):
        """Moderate reaction (often) should apply moderate penalty."""
        profile = empty_profile.copy()
        profile["repeated_negative_reactions"] = [
            {
                "ingredient": "fragrance",
                "reaction": "redness",
                "frequency": "often",
            }
        ]
        
        safety_score = 100
        final_cap = 100
        ingredients = ["water", "fragrance", "glycerin"]
        
        new_safety, new_cap = apply_repeated_reactions_to_scores(
            profile=profile,
            ingredients_list=ingredients,
            current_safety_score=safety_score,
            current_final_cap=final_cap,
        )
        
        assert new_safety < safety_score
        assert new_cap < final_cap
        # Moderate should be less severe than "always"
        assert new_safety > 0  # Not zero like severe
    
    def test_mild_reaction_small_penalty(self, empty_profile):
        """Mild reaction (sometimes) should apply small penalty."""
        profile = empty_profile.copy()
        profile["repeated_negative_reactions"] = [
            {
                "ingredient": "alcohol",
                "reaction": "dryness",
                "frequency": "sometimes",
            }
        ]
        
        safety_score = 100
        final_cap = 100
        ingredients = ["water", "alcohol", "glycerin"]
        
        new_safety, new_cap = apply_repeated_reactions_to_scores(
            profile=profile,
            ingredients_list=ingredients,
            current_safety_score=safety_score,
            current_final_cap=final_cap,
        )
        
        assert new_safety < safety_score
        # Mild should be less severe than moderate
        assert new_safety > 50  # Still relatively high
    
    def test_reaction_not_in_ingredients_no_change(self, empty_profile):
        """Reaction to ingredient not in list should not change scores."""
        profile = empty_profile.copy()
        profile["repeated_negative_reactions"] = [
            {
                "ingredient": "SLS",
                "reaction": "itching",
                "frequency": "always",
            }
        ]
        
        safety_score = 100
        final_cap = 100
        ingredients = ["water", "glycerin"]  # No SLS
        
        new_safety, new_cap = apply_repeated_reactions_to_scores(
            profile=profile,
            ingredients_list=ingredients,
            current_safety_score=safety_score,
            current_final_cap=final_cap,
        )
        
        assert new_safety == safety_score
        assert new_cap == final_cap


class TestEnsureList:
    """Tests for _ensure_list helper function."""
    
    def test_none_returns_empty_list(self):
        """None should return empty list."""
        result = _ensure_list(None)
        assert result == []
        assert isinstance(result, list)
    
    def test_list_returns_same_list(self):
        """List should return unchanged."""
        input_list = ["a", "b", "c"]
        result = _ensure_list(input_list)
        assert result == input_list
        assert result is input_list
    
    def test_string_returns_list_with_string(self):
        """String should return list containing that string."""
        result = _ensure_list("test")
        assert result == ["test"]
        assert isinstance(result, list)
    
    def test_number_returns_list_with_number(self):
        """Number should return list containing that number."""
        result = _ensure_list(42)
        assert result == [42]
        assert isinstance(result, list)

