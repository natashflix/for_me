"""
Unit tests for system helper functions.
"""

import pytest
from src.system import ForMeSystem


class TestIsProfileIncomplete:
    """Tests for _is_profile_incomplete helper function."""
    
    def test_empty_profile_is_incomplete(self):
        """Empty profile should be considered incomplete."""
        system = ForMeSystem(use_persistent_storage=False)
        profile = {}
        
        assert system._is_profile_incomplete(profile) is True
    
    def test_profile_with_food_strict_avoid_is_complete(self):
        """Profile with food_strict_avoid should be complete."""
        system = ForMeSystem(use_persistent_storage=False)
        profile = {
            "food_strict_avoid": [{"ingredient": "peanut", "type": "allergen"}],
        }
        
        assert system._is_profile_incomplete(profile) is False
    
    def test_profile_with_cosmetics_sensitivities_is_complete(self):
        """Profile with cosmetics_sensitivities should be complete."""
        system = ForMeSystem(use_persistent_storage=False)
        profile = {
            "cosmetics_sensitivities": ["fragrance"],
        }
        
        assert system._is_profile_incomplete(profile) is False
    
    def test_profile_with_hair_goals_is_complete(self):
        """Profile with hair_goals should be complete."""
        system = ForMeSystem(use_persistent_storage=False)
        profile = {
            "hair_goals": ["hydration"],
        }
        
        assert system._is_profile_incomplete(profile) is False
    
    def test_profile_with_skin_goals_is_complete(self):
        """Profile with skin_goals should be complete."""
        system = ForMeSystem(use_persistent_storage=False)
        profile = {
            "skin_goals": ["hydration"],
        }
        
        assert system._is_profile_incomplete(profile) is False
    
    def test_profile_with_household_strict_avoid_is_complete(self):
        """Profile with household_strict_avoid should be complete."""
        system = ForMeSystem(use_persistent_storage=False)
        profile = {
            "household_strict_avoid": ["bleach"],
        }
        
        assert system._is_profile_incomplete(profile) is False

