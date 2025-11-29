"""
Food Compatibility Agent

Strict agent for analyzing food products.
Uses strict_avoid, prefer_avoid, ok_if_small from profile.
Direct matches → large penalties. Traces → moderate penalties.
"""

from typing import Dict, Any, List, Optional
from ..types import (
    UserProfile,
    IngredientRisks,
    IngredientList,
    ScoreResult,
    FoodContext,
)
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

from ..tools import parse_ingredients
from ..tools.category_dictionaries import FOOD_AVOID, FOOD_WARN, FOOD_POSITIVE
from .profile_agent import load_user_profile
from ..memory import apply_repeated_reactions_to_scores


def build_food_context(
    profile: UserProfile,
    ingredients_list: IngredientList,
    ingredient_risks: IngredientRisks,
) -> FoodContext:
    """
    Builds structured context for food product analysis.
    
    Combines:
    - User's long-term profile (strict_avoid, prefer_avoid)
    - Normalized ingredient list
    - Category-specific dictionaries (FOOD_AVOID, FOOD_WARN, FOOD_POSITIVE)
    - Risk mappings
    
    This explicit context engineering ensures the scoring logic sees
    only the most relevant information for decision-making.
    
    Args:
        profile: User profile from long-term memory
        ingredients_list: Normalized ingredient names
        ingredient_risks: Mapping of ingredient -> risk tags
    
    Returns:
        Structured context dictionary
    """
    return {
        "profile": {
            "food_strict_avoid": profile.get("food_strict_avoid", []),
            "food_prefer_avoid": profile.get("food_prefer_avoid", []),
            "food_ok_if_small": profile.get("food_ok_if_small", []),
            "repeated_negative_reactions": profile.get("repeated_negative_reactions", []),
        },
        "ingredients": ingredients_list,
        "ingredient_risks": ingredient_risks,
        "dictionaries": {
            "avoid": FOOD_AVOID,
            "warn": FOOD_WARN,
            "positive": FOOD_POSITIVE,
        },
    }


def calculate_food_scores(
    profile: UserProfile,
    ingredient_risks: IngredientRisks,
    ingredients_list: IngredientList,
) -> ScoreResult:
    """
    Calculates scores for FOOD products with STRICT logic.
    
    Rules:
    - Safety = 0 ONLY if strict_avoid allergen is present (explicit)
    - Safety ≈ 20 if strict_avoid allergen is present (traces)
    - Sensitivity affected by prefer_avoid and warnings
    - Match based on positive ingredients and nutritional goals
    
    Args:
        profile: User profile with food_strict_avoid, food_prefer_avoid
        ingredient_risks: Mapping of ingredient -> risk tags
        ingredients_list: List of normalized ingredient names
    
    Returns:
        Dictionary with scores and risk analysis
    """
    # Initialize scores
    safety_score = 100
    sensitivity_score = 100
    match_score = 50  # Start neutral
    final_cap = 100
    has_strict_allergen_explicit = False
    has_strict_allergen_traces = False
    
    from_profile_match: List[Dict[str, Any]] = []
    generic_risks: List[Dict[str, Any]] = []
    safety_issues: List[str] = []
    sensitivity_issues: List[str] = []
    
    # Get food-specific avoid lists from profile
    food_strict_avoid = profile.get("food_strict_avoid", [])
    food_prefer_avoid = profile.get("food_prefer_avoid", [])
    food_ok_if_small = profile.get("food_ok_if_small", [])
    
    # Normalize strict_avoid for quick lookup
    strict_avoid_set = set()
    strict_avoid_normalized: Dict[str, Dict[str, Any]] = {}
    for item in food_strict_avoid:
        if isinstance(item, dict):
            ing = item.get("ingredient", "").lower().strip()
            if ing:
                strict_avoid_set.add(ing)
                strict_avoid_normalized[ing] = item
        elif isinstance(item, str):
            key = item.lower().strip()
            strict_avoid_set.add(key)
            strict_avoid_normalized[key] = {"ingredient": item, "type": "allergen"}
    
    # Normalize prefer_avoid for quick lookup
    prefer_avoid_list: List[str] = []
    for prefer_item in food_prefer_avoid:
        if isinstance(prefer_item, dict):
            ing = prefer_item.get("ingredient", "").lower().strip()
            if ing:
                prefer_avoid_list.append(ing)
        elif isinstance(prefer_item, str):
            prefer_avoid_list.append(prefer_item.lower().strip())
    
    # Tags we consider "risks" from risk agent
    risk_sensitivity_tags = {
        "high_salt",
        "high_sugar",
        "flavor_enhancer",
        "sweetener",
        "msg",
    }
    
    # Check each ingredient
    for ingredient in ingredients_list:
        ingredient_lower = ingredient.lower()
        matched = False
        tags_for_ingredient = ingredient_risks.get(ingredient, [])
        
        # ---- SAFETY: strict_avoid (CRITICAL) ----

        for strict_ing, strict_info in strict_avoid_normalized.items():
            if strict_ing and (strict_ing in ingredient_lower or ingredient_lower in strict_ing):
                # Check if it's "traces" or explicit
                is_traces = any(
                    keyword in ingredient_lower
                    for keyword in ["traces", "may contain", "produced", "production", "manufactured"]
                )
                
                if not is_traces:
                    # Explicit allergen - CRITICAL
                    has_strict_allergen_explicit = True
                    safety_score = 0
                    final_cap = min(final_cap, 15)
                    safety_issues.append(
                        f"{ingredient}: contains component from strict_avoid list ({strict_ing})"
                    )
                    from_profile_match.append({
                        "ingredient": ingredient,
                        "type": "strict_allergen_explicit",
                        "severity": "critical",
                        "category": "food"
                    })
                else:
                    # Traces - moderate penalty
                    has_strict_allergen_traces = True
                    safety_score = min(safety_score, 20)
                    final_cap = min(final_cap, 40)
                    safety_issues.append(
                        f"{ingredient}: may contain traces of component from strict_avoid ({strict_ing})"
                    )
                    from_profile_match.append({
                        "ingredient": ingredient,
                        "type": "strict_allergen_traces",
                        "severity": "high",
                        "category": "food"
                    })
                matched = True
                break
        
        # ---- SENSITIVITY: prefer_avoid (do NOT touch Safety) ----

        if not matched:
            for prefer_ing in prefer_avoid_list:
                if prefer_ing and (prefer_ing in ingredient_lower or ingredient_lower in prefer_ing):
                    sensitivity_score = max(0, sensitivity_score - 15)
                    sensitivity_issues.append(
                        f"{ingredient}: you prefer to avoid components of type '{prefer_ing}'"
                    )
                    from_profile_match.append({
                        "ingredient": ingredient,
                        "type": "prefer_avoid",
                        "severity": "medium",
                        "category": "food"
                    })
                    matched = True
                    break
        
        # ---- SENSITIVITY: FOOD_WARN dictionary ----

        if not matched:
            for warn_key, warn_tags in FOOD_WARN.items():
                if warn_key.lower() in ingredient_lower:
                    sensitivity_score = max(0, sensitivity_score - 10)
                    sensitivity_issues.append(
                        f"{ingredient}: contains component from warning zone ({warn_key})"
                    )
                    generic_risks.append({
                        "ingredient": ingredient,
                        "reason": f"contains {warn_key}",
                        "type": "warning",
                        "category": "food"
                    })
                    matched = True
                    break
        
        # ---- SENSITIVITY: risk tags from ingredient_risks ----

        # high_salt, high_sugar, flavor_enhancer, sweetener, msg
        for tag in tags_for_ingredient:
            tag_lower = tag.lower()
            if tag_lower in risk_sensitivity_tags:
                # Soft penalty if we haven't already accounted for this as prefer_avoid / warn
                sensitivity_score = max(0, sensitivity_score - 10)
                sensitivity_issues.append(
                    f"{ingredient}: contains risk factor ({tag_lower})"
                )
                generic_risks.append({
                    "ingredient": ingredient,
                    "reason": f"risk tag: {tag_lower}",
                    "type": "risk_tag",
                    "category": "food"
                })
                break
        
        # ---- MATCH: FOOD_POSITIVE (beneficial components) ----

        for pos_key, pos_tags in FOOD_POSITIVE.items():
            if pos_key.lower() in ingredient_lower:
                match_score = min(100, match_score + 10)
                break
    
    # Apply repeated negative reactions from long-term memory
    safety_score, final_cap = apply_repeated_reactions_to_scores(
        profile=profile,
        ingredients_list=ingredients_list,
        current_safety_score=safety_score,
        current_final_cap=final_cap,
    )
    
    # Calculate final FOR ME score
    from .scoring_weights import (
        FOOD_SAFETY_WEIGHT,
        FOOD_SENSITIVITY_WEIGHT,
        FOOD_MATCH_WEIGHT,
    )
    for_me_score = int(
        FOOD_SAFETY_WEIGHT * safety_score
        + FOOD_SENSITIVITY_WEIGHT * sensitivity_score
        + FOOD_MATCH_WEIGHT * match_score
    )
    
    # Apply final_cap
    for_me_score = min(for_me_score, final_cap)
    
    return {
        "status": "success",
        "safety_score": safety_score,
        "sensitivity_score": sensitivity_score,
        "match_score": match_score,
        "for_me_score": for_me_score,
        "final_cap": final_cap,
        "has_strict_allergen_explicit": has_strict_allergen_explicit,
        "has_strict_allergen_traces": has_strict_allergen_traces,
        "risk_analysis": {
            "from_profile_match": from_profile_match,
            "generic_risks": generic_risks
        },
        "safety_issues": safety_issues,
        "sensitivity_issues": sensitivity_issues,
        "category": "food"
    }


def create_food_compatibility_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Creates Food Compatibility Agent with STRICT scoring logic.
    
    Args:
        retry_config: HTTP retry configuration
    
    Returns:
        Configured FoodCompatibilityAgent
    """
    food_agent = LlmAgent(
        name="food_compatibility_agent",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        description="Analyzes FOOD products with strict safety rules. Safety=0 only for strict_avoid allergens.",
        instruction="""You are the Food Compatibility Agent for FOR ME.

CRITICAL RULES FOR FOOD:

1. SAFETY SCORE (0-100):
   - Safety = 0 ONLY if strict_avoid allergen is detected (explicit in composition)
   - Safety ≈ 20 if "traces" of strict_avoid allergen are detected
   - final_cap = 15 for explicit allergens, 40 for traces
   - Do NOT reduce Safety for prefer_avoid or warnings

2. SENSITIVITY SCORE (0-100):
   - Affected by: prefer_avoid, high_salt, high_sugar, MSG, sweeteners
   - Penalty: -15 for prefer_avoid, -10 for warnings
   - Does NOT affect Safety

3. MATCH SCORE (0-100):
   - Positives: fiber, protein, vitamins, omega-3, antioxidants
   - Negatives: absence of beneficial components
   - Considers nutritional goals from profile

4. PHRASING:
   - For strict_avoid: "you indicated that you strictly avoid [ingredient]"
   - For prefer_avoid: "you prefer to avoid [ingredient]"
   - NEVER use: "allergy", "diagnosis", "medical"

5. OUTPUT:
   🎯 FOR ME Score: X/100
   📊 Details:
      Safety Score: X/100
      Sensitivity Score: X/100
      Match Score: X/100
   ⚠️ Detected issues (only from profile)
   ✅ Positive aspects (if any)

Important: Food = safety filter. Be strict with allergens, but soft with preferences.
""",
        tools=[load_user_profile, parse_ingredients],
    )
    
    return food_agent
