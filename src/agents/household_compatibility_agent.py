"""
Household Compatibility Agent

Medium strictness for household cleaning products.
Strictness level between food and cosmetics.
"""

from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

from ..tools import parse_ingredients
from ..tools.category_dictionaries import HOUSEHOLD_RISK, HOUSEHOLD_WARN, HOUSEHOLD_POSITIVE
from .profile_agent import load_user_profile
from ..memory import apply_repeated_reactions_to_scores


def build_household_context(
    profile: Dict[str, Any],
    ingredients_list: List[str],
    ingredient_risks: Dict[str, List[str]],
) -> Dict[str, Any]:
    """
    Builds structured context for household product analysis.
    
    Combines:
    - User's long-term profile (household_strict_avoid, household_sensitivities)
    - Normalized ingredient list
    - Category-specific dictionaries (HOUSEHOLD_RISK, HOUSEHOLD_WARN, HOUSEHOLD_POSITIVE)
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
            "household_strict_avoid": profile.get("household_strict_avoid", []),
            "household_sensitivities": profile.get("household_sensitivities", []),
            "repeated_negative_reactions": profile.get("repeated_negative_reactions", []),
        },
        "ingredients": ingredients_list,
        "ingredient_risks": ingredient_risks,
        "dictionaries": {
            "risk": HOUSEHOLD_RISK,
            "warn": HOUSEHOLD_WARN,
            "positive": HOUSEHOLD_POSITIVE,
        },
    }


def calculate_household_scores(
    profile: Dict[str, Any],
    ingredient_risks: Dict[str, List[str]],
    ingredients_list: List[str],
) -> Dict[str, Any]:
    """
    Calculates scores for HOUSEHOLD products with MEDIUM strictness.
    
    Rules:
    - Safety affected by strict_avoid (bleach, ammonia, etc.)
    - Sensitivity affected by irritants (fragrance, SLS, etc.)
    - Match based on eco-friendly ingredients
    
    Args:
        profile: User profile with household_strict_avoid, household_sensitivities
        ingredient_risks: Mapping of ingredient -> risk tags
        ingredients_list: List of normalized ingredient names
    
    Returns:
        Dictionary with scores and risk analysis
    """
    # Initialize scores
    safety_score = 100
    sensitivity_score = 100
    match_score = 50
    final_cap = 100
    
    from_profile_match = []
    generic_risks = []
    
    # Get household-specific data from profile
    household_strict_avoid = profile.get("household_strict_avoid", [])
    household_sensitivities = profile.get("household_sensitivities", [])
    
    # Normalize strict_avoid
    strict_avoid_set = set()
    strict_avoid_normalized = {}
    for item in household_strict_avoid:
        if isinstance(item, dict):
            ing = item.get("ingredient", "").lower().strip()
            strict_avoid_set.add(ing)
            strict_avoid_normalized[ing] = item
        elif isinstance(item, str):
            strict_avoid_set.add(item.lower().strip())
            strict_avoid_normalized[item.lower().strip()] = {"ingredient": item, "type": "toxic"}
    
    # Check each ingredient
    for ingredient in ingredients_list:
        ingredient_lower = ingredient.lower()
        matched = False
        
        # Check strict_avoid (affects Safety)
        for strict_ing, strict_info in strict_avoid_normalized.items():
            if strict_ing in ingredient_lower or ingredient_lower in strict_ing:
                safety_score = 0
                final_cap = min(final_cap, 20)  # Less strict than food
                from_profile_match.append({
                    "ingredient": ingredient,
                    "type": "strict_avoid",
                    "severity": "critical",
                    "category": "household"
                })
                matched = True
                break
        
        # Check HOUSEHOLD_RISK (only if in strict_avoid)
        if not matched:
            for risk_key, risk_tags in HOUSEHOLD_RISK.items():
                if risk_key.lower() in ingredient_lower:
                    # Only penalize if user has it in strict_avoid
                    if any(risk_key.lower() in sa.lower() for sa in strict_avoid_set):
                        safety_score = 0
                        final_cap = min(final_cap, 20)
                        from_profile_match.append({
                            "ingredient": ingredient,
                            "type": "strict_avoid",
                            "severity": "critical",
                            "category": "household"
                        })
                    else:
                        # Just a warning
                        sensitivity_score = max(0, sensitivity_score - 10)
                        generic_risks.append({
                            "ingredient": ingredient,
                            "reason": f"contains {risk_key}",
                            "type": "warning",
                            "category": "household"
                        })
                    matched = True
                    break
        
        # Check household_sensitivities (affects Sensitivity)
        if not matched:
            for sens in household_sensitivities:
                sens_lower = sens.lower().strip()
                if sens_lower in ingredient_lower or ingredient_lower in sens_lower:
                    sensitivity_score = max(0, sensitivity_score - 15)
                    from_profile_match.append({
                        "ingredient": ingredient,
                        "type": "sensitivity",
                        "severity": "medium",
                        "category": "household"
                    })
                    matched = True
                    break
        
        # Check HOUSEHOLD_WARN (affects Sensitivity)
        if not matched:
            for warn_key, warn_tags in HOUSEHOLD_WARN.items():
                if warn_key.lower() in ingredient_lower:
                    sensitivity_score = max(0, sensitivity_score - 10)
                    generic_risks.append({
                        "ingredient": ingredient,
                        "reason": f"may be an irritant ({warn_key})",
                        "type": "irritant",
                        "category": "household"
                    })
                    break
        
        # Check HOUSEHOLD_POSITIVE (affects Match)
        for pos_key, pos_tags in HOUSEHOLD_POSITIVE.items():
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
        HOUSEHOLD_SAFETY_WEIGHT,
        HOUSEHOLD_SENSITIVITY_WEIGHT,
        HOUSEHOLD_MATCH_WEIGHT,
    )
    for_me_score = int(
        HOUSEHOLD_SAFETY_WEIGHT * safety_score +
        HOUSEHOLD_SENSITIVITY_WEIGHT * sensitivity_score +
        HOUSEHOLD_MATCH_WEIGHT * match_score
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
        "category": "household"
    }


def create_household_compatibility_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Creates Household Compatibility Agent with MEDIUM strictness.
    
    Args:
        retry_config: HTTP retry configuration
    
    Returns:
        Configured HouseholdCompatibilityAgent
    """
    household_agent = LlmAgent(
        name="household_compatibility_agent",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        description="Analyzes HOUSEHOLD products with medium strictness. Between food and cosmetics.",
        instruction="""You are the Household Compatibility Agent for FOR ME.

CRITICAL RULES FOR HOUSEHOLD:

1. SAFETY SCORE (0-100):
   - Safety = 0 if strict_avoid is detected (bleach, ammonia, etc.)
   - Safety does NOT drop for irritants, only for toxic substances from strict_avoid
   - final_cap = 20 (less strict than food)

2. SENSITIVITY SCORE (0-100):
   - Affected by: fragrance, SLS, SLES, phosphates, synthetic dyes
   - Penalty: -10-15 for irritants
   - These are warnings, not critical issues

3. MATCH SCORE (0-100):
   - Positives: plant-based, biodegradable, enzymes, natural cleaning agents
   - Considers eco-friendly preferences

4. PHRASING:
   - For strict_avoid: "you indicated that you strictly avoid [ingredient]"
   - For irritants: "may be an irritant"
   - NEVER use: "allergy", "diagnosis"

5. OUTPUT:
   🎯 FOR ME Score: X/100
   📊 Details:
      Safety Score: X/100
      Sensitivity Score: X/100
      Match Score: X/100
   ⚠️ Detected issues (only from profile)
   ✅ Positive aspects (if any)

Important: Household = medium strictness. Be attentive to toxic substances, but soft with irritants.
""",
        tools=[load_user_profile, parse_ingredients],
    )
    
    return household_agent
