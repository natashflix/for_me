"""
Unit tests for tool functions (parsing, risk dictionary).
"""

import pytest
from src.tools.ingredient_parser import parse_ingredients
from src.tools.risk_dictionary import get_ingredient_risks
from tests.conftest import mock_tool_context


class TestIngredientParser:
    """Tests for parse_ingredients function."""
    
    def test_parse_comma_separated(self, mock_tool_context):
        """Should parse comma-separated ingredients."""
        text = "water, sodium lauryl sulfate, glycerin, fragrance"
        result = parse_ingredients(mock_tool_context, text)
        
        assert result["status"] == "success"
        assert "water" in result["ingredients"]
        assert "sodium lauryl sulfate" in result["ingredients"]
        assert "glycerin" in result["ingredients"]
        assert "fragrance" in result["ingredients"]
        assert result["count"] == 4
    
    def test_parse_newline_separated(self, mock_tool_context):
        """Should parse newline-separated ingredients."""
        text = "water\nsodium lauryl sulfate\nglycerin"
        result = parse_ingredients(mock_tool_context, text)
        
        assert result["status"] == "success"
        assert len(result["ingredients"]) == 3
        assert "water" in result["ingredients"]
    
    def test_parse_mixed_delimiters(self, mock_tool_context):
        """Should parse ingredients with mixed delimiters."""
        text = "water, sodium lauryl sulfate; glycerin\nfragrance"
        result = parse_ingredients(mock_tool_context, text)
        
        assert result["status"] == "success"
        assert len(result["ingredients"]) >= 3
    
    def test_normalize_lowercase(self, mock_tool_context):
        """Should normalize to lowercase."""
        text = "WATER, Sodium Lauryl Sulfate, GLYCERIN"
        result = parse_ingredients(mock_tool_context, text)
        
        assert result["status"] == "success"
        assert "water" in result["ingredients"]
        assert "sodium lauryl sulfate" in result["ingredients"]
        assert "glycerin" in result["ingredients"]
    
    def test_remove_numbering(self, mock_tool_context):
        """Should remove leading numbers and formatting."""
        text = "1. water, 2. sodium lauryl sulfate, 3. glycerin"
        result = parse_ingredients(mock_tool_context, text)
        
        assert result["status"] == "success"
        assert "water" in result["ingredients"]
        assert "sodium lauryl sulfate" in result["ingredients"]
        assert "glycerin" in result["ingredients"]
        # Should not contain "1.", "2.", etc.
        assert not any("1." in ing or "2." in ing for ing in result["ingredients"])
    
    def test_empty_text_error(self, mock_tool_context):
        """Should return error for empty text."""
        result = parse_ingredients(mock_tool_context, "")
        assert result["status"] == "error"
        assert "error_message" in result
    
    def test_whitespace_only_error(self, mock_tool_context):
        """Should return error for whitespace-only text."""
        result = parse_ingredients(mock_tool_context, "   \n\t  ")
        assert result["status"] == "error"
    
    def test_extract_parentheses_content(self, mock_tool_context):
        """Should extract important content from parentheses."""
        text = "flavoring substances (contains dairy derivatives)"
        result = parse_ingredients(mock_tool_context, text)
        
        assert result["status"] == "success"
        # Should contain both main ingredient and extracted content
        assert any("dairy" in ing.lower() or "derivatives" in ing.lower() 
                  for ing in result["ingredients"])


class TestRiskDictionary:
    """Tests for get_ingredient_risks function."""
    
    def test_exact_match(self, mock_tool_context):
        """Should find exact matches in risk dictionary."""
        ingredients = ["fragrance", "SLS", "parabens"]
        result = get_ingredient_risks(mock_tool_context, ingredients)
        
        assert result["status"] == "success"
        assert "fragrance" in result["risks"]
        assert "irritant" in result["risks"]["fragrance"] or "fragrance" in result["risks"]["fragrance"]
        # SLS should be found (case-insensitive matching)
        assert "SLS" in result["risks"] or any("sls" in k.lower() for k in result["risks"].keys())
    
    def test_partial_match(self, mock_tool_context):
        """Should find partial matches (ingredient contains key)."""
        ingredients = ["sodium lauryl sulfate"]
        result = get_ingredient_risks(mock_tool_context, ingredients)
        
        assert result["status"] == "success"
        # Should match "SLS" or "sodium lauryl sulfate"
        assert len(result["risks"]) > 0
    
    def test_no_risks_found(self, mock_tool_context):
        """Should return empty list for ingredients with no risks."""
        ingredients = ["water", "glycerin", "unknown_ingredient_xyz"]
        result = get_ingredient_risks(mock_tool_context, ingredients)
        
        assert result["status"] == "success"
        # All ingredients should be in risks dict, but some may have empty lists
        assert len(result["risks"]) == len(ingredients)
    
    def test_empty_list_error(self, mock_tool_context):
        """Should return error for empty ingredients list."""
        result = get_ingredient_risks(mock_tool_context, [])
        assert result["status"] == "error"
        assert "error_message" in result
    
    def test_all_risk_tags_collected(self, mock_tool_context):
        """Should collect all unique risk tags."""
        ingredients = ["fragrance", "parabens", "SLS"]
        result = get_ingredient_risks(mock_tool_context, ingredients)
        
        assert result["status"] == "success"
        assert "all_risk_tags" in result
        assert isinstance(result["all_risk_tags"], list)
        assert len(result["all_risk_tags"]) > 0
    
    def test_ingredients_with_risks_count(self, mock_tool_context):
        """Should count ingredients with risks."""
        ingredients = ["fragrance", "water", "parabens"]
        result = get_ingredient_risks(mock_tool_context, ingredients)
        
        assert result["status"] == "success"
        assert "ingredients_with_risks" in result
        assert result["ingredients_with_risks"] >= 0
        assert result["ingredients_with_risks"] <= len(ingredients)
    
    def test_case_insensitive(self, mock_tool_context):
        """Should handle case-insensitive matching."""
        ingredients = ["FRAGRANCE", "SlS", "Parabens"]
        result = get_ingredient_risks(mock_tool_context, ingredients)
        
        assert result["status"] == "success"
        # Should find matches regardless of case
        assert len(result["risks"]) > 0

