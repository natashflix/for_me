"""
Category-specific tools for routing and analysis.

Tools for determining product category and calling appropriate agents.
"""

from typing import Dict, Any, Optional
from google.adk.tools.tool_context import ToolContext

from ..tools import parse_ingredients, get_ingredient_risks
from .food_compatibility_agent import calculate_food_scores
from .cosmetics_compatibility_agent import calculate_cosmetics_scores
from .household_compatibility_agent import calculate_household_scores
from .profile_agent import load_user_profile


def detect_product_category(
    tool_context: ToolContext,
    ingredient_text: str,
    product_domain: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Detects product category (food, cosmetics, household) based on:
    - Explicit product_domain parameter
    - Ingredient keywords
    - Product composition
    
    Args:
        tool_context: ADK tool context
        ingredient_text: Raw ingredient list text
        product_domain: Optional explicit domain hint
    
    Returns:
        Dictionary with detected category
    """
    # If domain is explicitly provided, use it
    if product_domain:
        domain_lower = product_domain.lower()
        if domain_lower in ["food", "еда", "продукт питания", "beverage", "snack"]:
            return {"status": "success", "category": "food"}
        elif domain_lower in ["cosmetics", "косметика", "skincare", "haircare", "makeup", "уход"]:
            return {"status": "success", "category": "cosmetics"}
        elif domain_lower in ["household", "бытовая химия", "cleaning", "detergent", "моющее"]:
            return {"status": "success", "category": "household"}
    
    # Parse ingredients to detect category (via tool, with tool_context)
    parsed_result = parse_ingredients(
        tool_context=tool_context,
        ingredient_text=ingredient_text,
    )
    if parsed_result["status"] != "success":
        return {"status": "error", "error_message": "Failed to parse ingredients"}
    
    ingredients_list = parsed_result["ingredients"]
    ingredients_text_lower = " ".join(ingredients_list).lower()
    
    # FOOD keywords
    food_keywords = [
        "молоко", "milk", "dairy", "lactose", "whey", "casein",
        "пшеница", "wheat", "gluten", "мука", "flour",
        "сахар", "sugar", "sucrose", "fructose",
        "соль", "salt", "sodium",
        "орехи", "nuts", "peanut", "almond",
        "яйцо", "egg", "eggs",
        "краситель", "coloring", "yellow-5", "tartrazine",
        "усилитель вкуса", "msg", "глутамат",
        "консервант", "preservative",
    ]
    
    # COSMETICS keywords
    cosmetics_keywords = [
        "aqua", "water", "eau",
        "sodium lauryl", "sodium laureth", "sls", "sles",
        "dimethicone", "silicone", "силикон",
        "glycerin", "глицерин",
        "parfum", "fragrance", "отдушка",
        "niacinamide", "ниацинамид",
        "ceramides", "церамиды",
        "hyaluronic", "гиалуроновая",
        "panthenol", "пантенол",
        "phenoxyethanol",
        "carbomer",
        "shampoo", "шампунь", "conditioner", "кондиционер",
        "serum", "сыворотка", "cream", "крем",
    ]
    
    # HOUSEHOLD keywords
    household_keywords = [
        "bleach", "отбеливатель", "хлор", "chlorine",
        "ammonia", "аммиак",
        "detergent", "моющее",
        "surfactant", "поверхностно-активное",
        "phosphates", "фосфаты",
        "sodium hypochlorite", "гипохлорит",
        "triclosan", "триклозан",
        "cleaning", "чистящее",
    ]
    
    # Count matches
    food_matches = sum(1 for kw in food_keywords if kw in ingredients_text_lower)
    cosmetics_matches = sum(1 for kw in cosmetics_keywords if kw in ingredients_text_lower)
    household_matches = sum(1 for kw in household_keywords if kw in ingredients_text_lower)
    
    # Determine category
    if household_matches > 0 and household_matches >= cosmetics_matches:
        category = "household"
    elif cosmetics_matches > 0 and cosmetics_matches >= food_matches:
        category = "cosmetics"
    elif food_matches > 0:
        category = "food"
    else:
        # Default to cosmetics if unclear (most common case)
        category = "cosmetics"
    
    return {
        "status": "success",
        "category": category,
        "confidence": "high" if max(food_matches, cosmetics_matches, household_matches) > 2 else "medium"
    }


def analyze_food_product(
    tool_context: ToolContext,
    user_id: str,
    ingredient_text: str,
) -> Dict[str, Any]:
    """
    Analyzes FOOD product using FoodCompatibilityAgent logic.
    
    This function implements the agent-as-a-tool pattern:
    1. Loads user profile from long-term memory
    2. Parses and normalizes ingredient list
    3. Gets risk mappings
    4. Builds structured context (via build_food_context)
    5. Calculates scores using strict food logic
    """
    # Load profile from long-term memory
    profile_result = load_user_profile(tool_context=tool_context, user_id=user_id)
    profile = profile_result.get("profile", {}) if isinstance(profile_result, dict) and "profile" in profile_result else profile_result
    
    # Parse ingredients using Ingredient Parser Tool
    parsed_result = parse_ingredients(
        tool_context=tool_context,
        ingredient_text=ingredient_text,
    )
    if parsed_result["status"] != "success":
        return {"status": "error", "error_message": "Failed to parse ingredients"}
    
    ingredients_list = parsed_result["ingredients"]
    
    # Get risks using Risk Dictionary Tool
    risks_result = get_ingredient_risks(
        tool_context=tool_context,
        ingredients=ingredients_list,
    )
    ingredient_risks = risks_result.get("risks", {}) if isinstance(risks_result, dict) else risks_result
    
    # Build structured context (context engineering)
    from .food_compatibility_agent import build_food_context
    context = build_food_context(
        profile=profile,
        ingredients_list=ingredients_list,
        ingredient_risks=ingredient_risks,
    )
    
    # Calculate scores using food logic
    scores_result = calculate_food_scores(
        profile=profile,
        ingredient_risks=ingredient_risks,
        ingredients_list=ingredients_list,
    )

    # Optionally save context as well — looks good for "context engineering"
    tool_context.state[f"analysis_result_{user_id}"] = scores_result
    tool_context.state["last_analysis_result"] = scores_result
    tool_context.state[f"context_{user_id}"] = context
    tool_context.state["last_context"] = context
    
    return scores_result


def analyze_cosmetics_product(
    tool_context: ToolContext,
    user_id: str,
    ingredient_text: str,
) -> Dict[str, Any]:
    """
    Analyzes COSMETICS product using CosmeticsCompatibilityAgent logic.
    """
    # Load profile from long-term memory
    profile_result = load_user_profile(tool_context=tool_context, user_id=user_id)
    profile = profile_result.get("profile", {}) if isinstance(profile_result, dict) and "profile" in profile_result else profile_result
    
    # Parse ingredients using Ingredient Parser Tool
    parsed_result = parse_ingredients(
        tool_context=tool_context,
        ingredient_text=ingredient_text,
    )
    if parsed_result["status"] != "success":
        return {"status": "error", "error_message": "Failed to parse ingredients"}
    
    ingredients_list = parsed_result["ingredients"]
    
    # Get risks using Risk Dictionary Tool
    risks_result = get_ingredient_risks(
        tool_context=tool_context,
        ingredients=ingredients_list,
    )
    ingredient_risks = risks_result.get("risks", {}) if isinstance(risks_result, dict) else risks_result
    
    # Build structured context (context engineering)
    from .cosmetics_compatibility_agent import build_cosmetics_context
    context = build_cosmetics_context(
        profile=profile,
        ingredients_list=ingredients_list,
        ingredient_risks=ingredient_risks,
    )
    
    # Calculate scores using cosmetics logic
    scores_result = calculate_cosmetics_scores(
        profile=profile,
        ingredient_risks=ingredient_risks,
        ingredients_list=ingredients_list,
    )
    
    # Store result in session state for retrieval by orchestrator
    tool_context.state[f"analysis_result_{user_id}"] = scores_result
    tool_context.state["last_analysis_result"] = scores_result
    tool_context.state[f"context_{user_id}"] = context
    tool_context.state["last_context"] = context
    
    return scores_result


def analyze_household_product(
    tool_context: ToolContext,
    user_id: str,
    ingredient_text: str,
) -> Dict[str, Any]:
    """
    Analyzes HOUSEHOLD product using HouseholdCompatibilityAgent logic.
    """
    # Load profile from long-term memory
    profile_result = load_user_profile(tool_context=tool_context, user_id=user_id)
    profile = profile_result.get("profile", {}) if isinstance(profile_result, dict) and "profile" in profile_result else profile_result
    
    # Parse ingredients using Ingredient Parser Tool
    parsed_result = parse_ingredients(
        tool_context=tool_context,
        ingredient_text=ingredient_text,
    )
    if parsed_result["status"] != "success":
        return {"status": "error", "error_message": "Failed to parse ingredients"}
    
    ingredients_list = parsed_result["ingredients"]
    
    # Get risks using Risk Dictionary Tool
    risks_result = get_ingredient_risks(
        tool_context=tool_context,
        ingredients=ingredients_list,
    )
    ingredient_risks = risks_result.get("risks", {}) if isinstance(risks_result, dict) else risks_result
    
    # Build structured context (context engineering)
    from .household_compatibility_agent import build_household_context
    context = build_household_context(
        profile=profile,
        ingredients_list=ingredients_list,
        ingredient_risks=ingredient_risks,
    )
    
    # Calculate scores using household logic
    scores_result = calculate_household_scores(
        profile=profile,
        ingredient_risks=ingredient_risks,
        ingredients_list=ingredients_list,
    )
    
    # Store result in session state for retrieval by orchestrator
    tool_context.state[f"analysis_result_{user_id}"] = scores_result
    tool_context.state["last_analysis_result"] = scores_result
    tool_context.state[f"context_{user_id}"] = context
    tool_context.state["last_context"] = context
    
    return scores_result
