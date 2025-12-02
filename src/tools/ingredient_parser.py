"""
Ingredient Parser Tool

Parses raw ingredient text into normalized list of ingredient names.
"""

import re
from typing import Dict, List
from google.adk.tools.tool_context import ToolContext


def parse_ingredients(tool_context: ToolContext, ingredient_text: str) -> Dict[str, any]:
    """
    Parses raw ingredient text into a normalized list of ingredient names.
    
    This tool extracts individual ingredients from a comma-separated or
    newline-separated ingredient list, normalizes them (lowercase, strip),
    and removes common formatting artifacts.
    
    Args:
        tool_context: ADK tool context
        ingredient_text: Raw text containing ingredient list.
                       Can be comma-separated, newline-separated, or mixed.
    
    Returns:
        Dictionary with status and parsed ingredients.
        Success: {"status": "success", "ingredients": ["ingredient1", "ingredient2", ...]}
        Error: {"status": "error", "error_message": "..."}
    """
    try:
        if not ingredient_text or not ingredient_text.strip():
            return {
                "status": "error",
                "error_message": "Empty ingredient text provided"
            }
        
        # Split by common delimiters (comma, semicolon, newline, bullet point)
        # Handle both comma-separated, newline-separated, and bullet-separated lists
        raw_ingredients = re.split(r'[,;\n•·]', ingredient_text)
        
        # Normalize each ingredient
        normalized = []
        for ingredient in raw_ingredients:
            # Strip whitespace and convert to lowercase
            cleaned = ingredient.strip().lower()
            
            # Skip empty strings
            if not cleaned:
                continue
            
            # Extract important information from parentheses
            # Example: "flavoring substances (contains dairy derivatives)" 
            # should also create entry for "dairy derivatives"
            paren_matches = re.findall(r'\(([^)]+)\)', cleaned)
            for match in paren_matches:
                # Check if parentheses contain important allergens/ingredients
                if any(keyword in match.lower() for keyword in [
                    'содержат', 'contains', 'производные', 'derived', 
                    'молок', 'milk', 'dairy', 'соя', 'soy', 'глютен', 'gluten'
                ]):
                    # Extract the key ingredient from parentheses
                    # "contains dairy derivatives" -> "dairy derivatives"
                    if 'производные' in match.lower() and 'молок' in match.lower():
                        normalized.append('dairy derivatives')
                    elif 'содержит' in match.lower() or 'содержат' in match.lower():
                        # Extract what comes after "contains"
                        after_contains = re.sub(r'.*содержит\s*', '', match, flags=re.IGNORECASE).strip()
                        if after_contains:
                            normalized.append(after_contains)
            
            # Remove common prefixes/suffixes that might be formatting artifacts
            # Remove leading numbers (e.g., "1. water" -> "water")
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', cleaned)
            
            # Keep parentheses content for now (we'll process it above)
            # But remove percentage indicators (e.g., "water (50%)" -> "water")
            cleaned = re.sub(r'\s*\([^)]*%[^)]*\)', '', cleaned)
            
            # Remove extra whitespace
            cleaned = ' '.join(cleaned.split())
            
            if cleaned:
                normalized.append(cleaned)
        
        if not normalized:
            return {
                "status": "error",
                "error_message": "No valid ingredients found after parsing"
            }
        
        # QA: detect duplicate ingredients before scoring
        # Remove exact duplicates while preserving order
        seen = set()
        deduplicated = []
        duplicates = []
        for ing in normalized:
            if ing not in seen:
                seen.add(ing)
                deduplicated.append(ing)
            else:
                duplicates.append(ing)
        
        # QA: flag unknown or unparsed tokens
        # Ingredients that are too short or look like formatting artifacts
        unknown_ingredients = []
        for ing in deduplicated:
            # Flag very short ingredients (likely parsing artifacts)
            if len(ing) < 2:
                unknown_ingredients.append(ing)
            # Flag ingredients that are just numbers or special chars
            elif ing.replace('.', '').replace('-', '').isdigit():
                unknown_ingredients.append(ing)
        
        return {
            "status": "success",
            "ingredients": deduplicated,
            "count": len(deduplicated),
            "qa_metadata": {
                "duplicates_removed": duplicates,
                "unknown_ingredients": unknown_ingredients,
                "original_count": len(normalized),
                "deduplicated_count": len(deduplicated)
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Parsing error: {str(e)}"
        }

