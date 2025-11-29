"""
Cosmetics Compatibility Agent

Soft agent for analyzing cosmetics and personal care products.
Safety does NOT drop if there is no strict_avoid.
Irritants affect Sensitivity, NOT Safety.
"""

from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

from ..tools import parse_ingredients
from ..tools.category_dictionaries import COSMETICS_NEGATIVE, COSMETICS_POSITIVE, COSMETICS_HAIR_SPECIFIC
from .profile_agent import load_user_profile
from ..memory import apply_repeated_reactions_to_scores


def build_cosmetics_context(
    profile: Dict[str, Any],
    ingredients_list: List[str],
    ingredient_risks: Dict[str, List[str]],
) -> Dict[str, Any]:
    """
    Builds structured context for cosmetics product analysis.
    
    Combines:
    - User's long-term profile (cosmetics_sensitivities, hair_type, hair_goals, skin_type, skin_goals)
    - Normalized ingredient list
    - Category-specific dictionaries (COSMETICS_NEGATIVE, COSMETICS_POSITIVE)
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
            "cosmetics_sensitivities": profile.get("cosmetics_sensitivities", []),
            "cosmetics_preferences": profile.get("cosmetics_preferences", []),
            "hair_type": profile.get("hair_type", ""),
            "hair_goals": profile.get("hair_goals", []),
            "skin_type": profile.get("skin_type", ""),
            "skin_goals": profile.get("skin_goals", []),
            "strict_avoid": profile.get("strict_avoid", []),
            "repeated_negative_reactions": profile.get("repeated_negative_reactions", []),
        },
        "ingredients": ingredients_list,
        "ingredient_risks": ingredient_risks,
        "dictionaries": {
            "negative": COSMETICS_NEGATIVE,
            "positive": COSMETICS_POSITIVE,
            "hair_specific": COSMETICS_HAIR_SPECIFIC,
        },
    }


def calculate_cosmetics_scores(
    profile: Dict[str, Any],
    ingredient_risks: Dict[str, List[str]],
    ingredients_list: List[str],
) -> Dict[str, Any]:
    """
    Calculates scores for COSMETICS products with SOFT logic.
    
    Rules:
    - Safety = 100 by default (if no strict_avoid)
    - Irritants (SLS, fragrance, etc.) affect Sensitivity, NOT Safety
    - Positive ingredients (glycerin, silicones) affect Match
    - Hair goals affect only Match
    
    Args:
        profile: User profile with cosmetics_sensitivities, hair_type, hair_goals
        ingredient_risks: Mapping of ingredient -> risk tags
        ingredients_list: List of normalized ingredient names
    
    Returns:
        Dictionary with scores and risk analysis
    """
    # Initialize scores - COSMETICS starts with high safety
    safety_score = 100  # Does NOT drop if no strict_avoid
    sensitivity_score = 100
    match_score = 50  # Start neutral
    final_cap = 100

    from_profile_match: List[Dict[str, Any]] = []
    generic_risks: List[Dict[str, Any]] = []
    safety_issues: List[str] = []
    sensitivity_issues: List[str] = []
    
    # Get cosmetics-specific data from profile
    cosmetics_sensitivities = profile.get("cosmetics_sensitivities", [])
    cosmetics_preferences = profile.get("cosmetics_preferences", [])
    hair_type = profile.get("hair_type", "")
    hair_goals = profile.get("hair_goals", [])
    skin_type = profile.get("skin_type", "")
    skin_goals = profile.get("skin_goals", [])
    
    # Check for strict_avoid (only thing that can lower Safety)
    strict_avoid = profile.get("strict_avoid", [])
    strict_avoid_set = set()
    for item in strict_avoid:
        if isinstance(item, dict):
            ing = item.get("ingredient", "").lower().strip()
            if ing:
                strict_avoid_set.add(ing)
        elif isinstance(item, str):
            strict_avoid_set.add(item.lower().strip())
    
    # Check each ingredient
    for ingredient in ingredients_list:
        ingredient_lower = ingredient.lower()
        matched = False
        tags_for_ingredient = ingredient_risks.get(ingredient, [])

        # ---- SAFETY: strict_avoid only ----

        for strict_ing in strict_avoid_set:
            if strict_ing in ingredient_lower or ingredient_lower in strict_ing:
                is_traces = any(
                    keyword in ingredient_lower
                    for keyword in ["traces", "may contain", "produced", "production", "manufactured"]
                )
                if not is_traces:
                    safety_score = 0
                    final_cap = min(final_cap, 15)
                    safety_issues.append(
                        f"{ingredient}: contains component from strict_avoid list ({strict_ing})"
                    )
                    from_profile_match.append({
                        "ingredient": ingredient,
                        "type": "strict_allergen_explicit",
                        "severity": "critical",
                        "category": "cosmetics"
                    })
                else:
                    safety_score = min(safety_score, 20)
                    final_cap = min(final_cap, 40)
                    safety_issues.append(
                        f"{ingredient}: may contain traces of component from strict_avoid ({strict_ing})"
                    )
                    from_profile_match.append({
                        "ingredient": ingredient,
                        "type": "strict_allergen_traces",
                        "severity": "high",
                        "category": "cosmetics"
                    })
                matched = True
                break
        
        # ---- SENSITIVITY: cosmetics_sensitivities from profile ----

        if not matched:
            for sens in cosmetics_sensitivities:
                sens_lower = sens.lower().strip()
                if sens_lower and (sens_lower in ingredient_lower or ingredient_lower in sens_lower):
                    sensitivity_score = max(0, sensitivity_score - 20)
                    sensitivity_issues.append(
                        f"{ingredient}: you indicated sensitivity to components of type '{sens}'"
                    )
                    from_profile_match.append({
                        "ingredient": ingredient,
                        "type": "sensitivity",
                        "severity": "medium",
                        "category": "cosmetics"
                    })
                    matched = True
                    break
        
        # ---- SENSITIVITY: COSMETICS_NEGATIVE dictionary (string match) ----

        if not matched:
            for neg_key, neg_tags in COSMETICS_NEGATIVE.items():
                if neg_key.lower() in ingredient_lower:
                    sensitivity_score = max(0, sensitivity_score - 15)
                    sensitivity_issues.append(
                        f"{ingredient}: may be an irritating component ({neg_key})"
                    )
                    generic_risks.append({
                        "ingredient": ingredient,
                        "reason": f"may be an irritant ({neg_key})",
                        "type": "irritant",
                        "category": "cosmetics"
                    })
                    matched = True
                    break

        # ---- SENSITIVITY: risk tags (if available from ingredient_risks) ----

        # Examples: fragrance, drying_alcohol, harsh_surfactant
        irritant_tags = {"fragrance", "drying_alcohol", "harsh_surfactant", "phenoxyethanol", "high_salt"}
        for tag in tags_for_ingredient:
            tag_lower = tag.lower()
            if tag_lower in irritant_tags:
                # soft penalty if we haven't already penalized this ingredient as irritant
                sensitivity_score = max(0, sensitivity_score - 10)
                sensitivity_issues.append(
                    f"{ingredient}: contains potential irritant ({tag_lower})"
                )
                generic_risks.append({
                    "ingredient": ingredient,
                    "reason": f"risk tag: {tag_lower}",
                    "type": "irritant_tag",
                    "category": "cosmetics"
                })
                break
        
        # ---- MATCH: COSMETICS_POSITIVE ----

        for pos_key, pos_tags in COSMETICS_POSITIVE.items():
            if pos_key.lower() in ingredient_lower:
                # Check if it matches hair goals
                if "hydration" in pos_tags and "hydration" in hair_goals:
                    match_score = min(100, match_score + 15)
                elif "anti_frizz" in pos_tags and "anti_frizz" in hair_goals:
                    match_score = min(100, match_score + 15)
                elif "curl_friendly" in pos_tags and hair_type == "curly":
                    match_score = min(100, match_score + 10)
                else:
                    match_score = min(100, match_score + 5)
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
        COSMETICS_SAFETY_WEIGHT,
        COSMETICS_SENSITIVITY_WEIGHT,
        COSMETICS_MATCH_WEIGHT,
    )
    for_me_score = int(
        COSMETICS_SAFETY_WEIGHT * safety_score
        + COSMETICS_SENSITIVITY_WEIGHT * sensitivity_score
        + COSMETICS_MATCH_WEIGHT * match_score
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
        "risk_analysis": {
            "from_profile_match": from_profile_match,
            "generic_risks": generic_risks
        },
        "safety_issues": safety_issues,
        "sensitivity_issues": sensitivity_issues,
        "category": "cosmetics"
    }


def create_cosmetics_compatibility_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Creates Cosmetics Compatibility Agent with SOFT scoring logic.
    
    Args:
        retry_config: HTTP retry configuration
    
    Returns:
        Configured CosmeticsCompatibilityAgent
    """
    cosmetics_agent = LlmAgent(
        name="cosmetics_compatibility_agent",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        description="Analyzes COSMETICS products with soft recommendations. Safety=100 unless strict_avoid present.",
        instruction="""You are the Cosmetics Compatibility Agent for FOR ME.

CRITICAL RULES FOR COSMETICS:

1. SAFETY SCORE (0-100):
   - Safety = 100 by default (if no strict_avoid)
   - Safety = 0 ONLY if strict_avoid allergen is detected
   - SLS, fragrance, phenoxyethanol do NOT affect Safety
   - Do NOT reduce Safety for irritants

2. SENSITIVITY SCORE (0-100):
   - Affected by: SLS, fragrance, phenoxyethanol, sodium chloride, alcohol
   - Penalty: -15-20 for irritants
   - These are SOFT recommendations, not critical issues

3. MATCH SCORE (0-100):
   - Positives: glycerin, silicones, niacinamide, ceramides
   - Considers hair_type and hair_goals (hydration, anti_frizz, curl_definition)
   - Considers skin_type and skin_goals
   - These are recommendations, not requirements

4. PHRASING:
   - Do NOT write "does not match your profile" for irritants
   - Write: "may be an irritant" or "may not suit you"
   - For positives: "matches your goal [goal]"
   - NEVER use: "allergy", "diagnosis"

5. OUTPUT:
   🎯 FOR ME Score: X/100
   📊 Details:
      Safety Score: X/100
      Sensitivity Score: X/100
      Match Score: X/100
   ⚠️ Potential irritants (soft recommendations)
   ✅ Positive aspects (goal alignment)

Important: Cosmetics = soft recommendations. Be gentle, don't scare the user.
""",
        tools=[load_user_profile, parse_ingredients],
    )
    
    return cosmetics_agent
