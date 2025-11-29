"""
Scoring Agent

Calculates FOR ME scores (Safety, Sensitivity, Match) based on profile and risks.
"""

from typing import Dict, Any, List, Optional, Union
from ..types import (
    UserProfile,
    IngredientRisks,
    RiskTags,
    ScoreResult,
)
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.code_executors import BuiltInCodeExecutor
from google.genai import types


def can_say_user_avoids(tag_or_ingredient: str, user_profile: Dict[str, Any]) -> bool:
    """
    Checks if we can say "you indicated in your profile" about this tag/ingredient.
    
    Args:
        tag_or_ingredient: Tag or ingredient name
        user_profile: User profile
    
    Returns:
        True only if the user EXPLICITLY specified this in their profile
    """
    avoid_categories = set(user_profile.get("avoid_categories", []))
    avoid_ingredients = set(user_profile.get("avoid_ingredients", []))
    
    # Check exact match
    if tag_or_ingredient.lower() in {a.lower() for a in avoid_categories}:
        return True
    if tag_or_ingredient.lower() in {a.lower() for a in avoid_ingredients}:
        return True
    
    # Check partial match for categories
    tag_lower = tag_or_ingredient.lower()
    for category in avoid_categories:
        if category.lower() in tag_lower or tag_lower in category.lower():
            return True
    
    return False


def calculate_scores(
    profile: UserProfile,
    ingredient_risks: IngredientRisks,
    all_risk_tags: Optional[RiskTags] = None,
) -> ScoreResult:
    """
    Calculates safety, sensitivity, and match scores.
    
    Separates:
    - from_profile_match: what is actually specified in the profile
    - generic_risks: general risks that the user did NOT specify
    
    Args:
        profile: User profile with avoid_categories, avoid_ingredients, goals
        ingredient_risks: Mapping of ingredient -> risk tags
        all_risk_tags: All unique risk tags found
    
    Returns:
        Dictionary with scores, reasoning, and separated risk analysis
    """
    # Safety Score (0-100): Based on allergens
    safety_score = 100
    has_allergen = False
    has_strict_allergen_explicit = False  # Explicit presence of strict_avoid allergen
    has_strict_allergen_traces = False  # "May contain traces" for strict_avoid
    final_cap = 100  # Maximum final score
    safety_issues: List[str] = []  # List of safety issues

    # Sensitivity Score (0-100): will be adjusted below
    sensitivity_issues: List[str] = []  # List of sensitivity issues

    # Separate risks into two categories
    from_profile_match = []  # What is actually specified in the profile
    generic_risks = []  # General risks that are not in the profile
    
    # Get data from profile
    avoid_categories = set(profile.get("avoid_categories", []))
    avoid_ingredients = set(profile.get("avoid_ingredients", []))
    
    # Get new fields for strictness levels
    strict_avoid = profile.get("strict_avoid", [])  # List of dicts {"ingredient": "...", "type": "allergen"}
    prefer_avoid = profile.get("prefer_avoid", [])  # List of dicts {"ingredient": "...", "type": "preference"}
    
    # Normalize strict_avoid and prefer_avoid for quick lookup
    strict_avoid_set = set()
    strict_avoid_normalized = {}  # ingredient_lower -> original dict
    for item in strict_avoid:
        if isinstance(item, dict):
            ing = item.get("ingredient", "").lower().strip()
            if ing:
                strict_avoid_set.add(ing)
                strict_avoid_normalized[ing] = item
        elif isinstance(item, str):
            key = item.lower().strip()
            strict_avoid_set.add(key)
            strict_avoid_normalized[key] = {"ingredient": item, "type": "allergen"}
    
    prefer_avoid_set = set()
    prefer_avoid_normalized = {}  # ingredient_lower -> original dict
    for item in prefer_avoid:
        if isinstance(item, dict):
            ing = item.get("ingredient", "").lower().strip()
            if ing:
                prefer_avoid_set.add(ing)
                prefer_avoid_normalized[ing] = item
        elif isinstance(item, str):
            key = item.lower().strip()
            prefer_avoid_set.add(key)
            prefer_avoid_normalized[key] = {"ingredient": item, "type": "preference"}
    
    # For backward compatibility: if old fields "allergies", "sensitivities" exist
    # convert them to new structure and UPDATE profile so can_say_user_avoids can see them too
    if "allergies" in profile and not avoid_categories and not avoid_ingredients:
        old_allergies = profile.get("allergies", [])
        old_sensitivities = profile.get("sensitivities", [])
        avoid_categories = set(old_sensitivities)  # sensitivities -> categories
        avoid_ingredients = set(old_allergies)  # allergies -> ingredients

        # Update profile for consistent logic
        profile = dict(profile)
        profile["avoid_categories"] = list(avoid_categories)
        profile["avoid_ingredients"] = list(avoid_ingredients)
    
    # Normalize for comparison
    avoid_categories_normalized = {c.lower().strip() for c in avoid_categories}
    avoid_ingredients_normalized = {i.lower().strip() for i in avoid_ingredients}
    
    # Mapping: what is specified in profile -> what tags/ingredients this means in product
    category_mapping = {
        "soy": ["soy", "soybean"],
        "gluten": ["gluten", "wheat", "barley", "rye", "flour"],
        "dairy": ["dairy", "milk", "lactose", "whey", "casein", "dairy_derivatives"],
        "milk": ["dairy", "milk", "lactose", "whey", "casein", "dairy_derivatives"],
        "high_salt": ["high_salt", "salt", "sodium"],
        "salt": ["high_salt", "salt", "sodium"],
        "flavor_enhancer": ["flavor_enhancer", "msg", "monosodium_glutamate"],
        "fragrance": ["fragrance", "parfum", "perfume"],
        "drying_alcohol": ["drying_alcohol", "alcohol", "ethanol", "denatured_alcohol"],
    }
    
    # Check PRODUCT INGREDIENTS
    seen_ingredients = set()  # To avoid duplicates
    
    # First check strict_avoid and prefer_avoid
    for ingredient, tags in ingredient_risks.items():
        ingredient_lower = ingredient.lower()
        matched_from_profile = False
        ingredient_key = ingredient_lower  # Key for deduplication
        
        # CHECK 1: strict_avoid (strict avoidance - allergens)
        for strict_ing, strict_info in strict_avoid_normalized.items():
            # Check exact or partial match
            if (
                strict_ing in ingredient_lower 
                or ingredient_lower in strict_ing 
                or any(strict_ing in tag.lower() or tag.lower() in strict_ing for tag in tags)
            ):
                # Check if there's indication of "traces" in composition
                is_traces = any(
                    keyword in ingredient_lower 
                    for keyword in ["traces", "may contain", "produced", "production", "manufactured"]
                )
                
                if not is_traces:
                    # Explicit presence of allergen
                    has_strict_allergen_explicit = True
                    has_allergen = True
                    safety_score = 0
                    final_cap = min(final_cap, 15)  # Final score no more than ~15
                    safety_issues.append(
                        f"{ingredient}: contains allergen from strict_avoid list ({strict_ing})"
                    )
                    if ingredient_key not in seen_ingredients:
                        seen_ingredients.add(ingredient_key)
                        from_profile_match.append({
                            "ingredient": ingredient,
                            "tag": "strict_avoid",
                            "profile_category": strict_ing,
                            "type": "strict_allergen_explicit",
                            "severity": "critical"
                        })
                else:
                    # "May contain traces"
                    has_strict_allergen_traces = True
                    has_allergen = True
                    safety_score = min(safety_score, 20)  # Safety ≈ 20
                    final_cap = min(final_cap, 40)  # Final score no higher than ~40
                    safety_issues.append(
                        f"{ingredient}: may contain traces of allergen from strict_avoid list ({strict_ing})"
                    )
                    if ingredient_key not in seen_ingredients:
                        seen_ingredients.add(ingredient_key)
                        from_profile_match.append({
                            "ingredient": ingredient,
                            "tag": "strict_avoid_traces",
                            "profile_category": strict_ing,
                            "type": "strict_allergen_traces",
                            "severity": "high"
                        })
                matched_from_profile = True
                break
        
        # CHECK 2: prefer_avoid (preference to avoid - less strict)
        if not matched_from_profile:
            for prefer_ing, prefer_info in prefer_avoid_normalized.items():
                if (
                    prefer_ing in ingredient_lower 
                    or ingredient_lower in prefer_ing 
                    or any(prefer_ing in tag.lower() or tag.lower() in prefer_ing for tag in tags)
                ):
                    # Soft penalty for prefer_avoid
                    safety_score = max(0, safety_score - 15)  # 15 point penalty
                    final_cap = min(final_cap, 70)  # Final score can be higher
                    safety_issues.append(
                        f"{ingredient}: contains component from prefer_avoid list ({prefer_ing})"
                    )
                    if ingredient_key not in seen_ingredients:
                        seen_ingredients.add(ingredient_key)
                        from_profile_match.append({
                            "ingredient": ingredient,
                            "tag": "prefer_avoid",
                            "profile_category": prefer_ing,
                            "type": "preference",
                            "severity": "medium"
                        })
                    matched_from_profile = True
                    break
        
        # Check match with avoid_categories from profile
        for category in avoid_categories_normalized:
            product_keywords = category_mapping.get(category, [category])
            
            # Check ingredient risk tags
            for tag in tags:
                tag_lower = tag.lower()
                # Check tag match with category keywords
                if any(kw.lower() in tag_lower or tag_lower in kw.lower() for kw in product_keywords):
                    if can_say_user_avoids(category, profile):
                        has_allergen = True
                        matched_from_profile = True
                        safety_issues.append(
                            f"{ingredient}: contains risk related to category you indicated ({category})"
                        )
                        if ingredient_key not in seen_ingredients:
                            seen_ingredients.add(ingredient_key)
                            from_profile_match.append({
                                "ingredient": ingredient,
                                "tag": tag,
                                "profile_category": category,
                                "type": "category"
                            })
                        break
            
            # Check ingredient name directly
            if not matched_from_profile:
                for keyword in product_keywords:
                    keyword_lower = keyword.lower()
                    # Check if keyword is contained in ingredient name
                    if keyword_lower in ingredient_lower or ingredient_lower in keyword_lower:
                        if can_say_user_avoids(category, profile):
                            has_allergen = True
                            matched_from_profile = True
                            safety_issues.append(
                                f"{ingredient}: matches category you indicated as undesirable ({category})"
                            )
                            if ingredient_key not in seen_ingredients:
                                seen_ingredients.add(ingredient_key)
                                from_profile_match.append({
                                    "ingredient": ingredient,
                                    "tag": "ingredient_match",
                                    "profile_category": category,
                                    "type": "category"
                                })
                            break
        
        # Check match with avoid_ingredients from profile
        for avoid_ing in avoid_ingredients_normalized:
            if avoid_ing in ingredient_lower or ingredient_lower in avoid_ing:
                if can_say_user_avoids(avoid_ing, profile):
                    has_allergen = True
                    matched_from_profile = True
                    safety_issues.append(
                        f"{ingredient}: contains ingredient you indicated as undesirable ({avoid_ing})"
                    )
                    if ingredient_key not in seen_ingredients:
                        seen_ingredients.add(ingredient_key)
                        from_profile_match.append({
                            "ingredient": ingredient,
                            "tag": "direct_match",
                            "profile_ingredient": avoid_ing,
                            "type": "ingredient"
                        })
        
        # If didn't match profile but has risks - add to generic_risks
        if not matched_from_profile and tags:
            for tag in tags:
                tag_lower = tag.lower()
                # Check if this is a known allergen/risk
                # And make sure it's NOT specified in profile
                is_generic_risk = tag_lower in [
                    "allergen", "soy", "gluten", "dairy", "milk", 
                    "flavor_enhancer"
                ]
                
                # Additional check: if tag indicates milk/gluten/soy,
                # but it's NOT specified in profile
                if is_generic_risk:
                    is_in_profile = False
                    for cat in avoid_categories_normalized:
                        if cat in ["dairy", "milk", "gluten", "soy"]:
                            product_kw = category_mapping.get(cat, [])
                            if any(kw.lower() == tag_lower for kw in product_kw):
                                is_in_profile = True
                                break
                    
                    if not is_in_profile and ingredient_key not in seen_ingredients:
                        generic_risks.append({
                            "ingredient": ingredient,
                            "tag": tag,
                            "type": "generic_allergen"
                        })
                        safety_issues.append(
                            f"{ingredient}: contains general potential allergen ({tag}), even if you didn't indicate it in profile"
                        )
    
    # If allergen from profile found → Safety Score = 0 and strong cap
    if has_allergen:
        safety_score = 0
        final_cap = min(final_cap, 20)
    else:
        # If no direct allergens, but there are other issues
        for ingredient, tags in ingredient_risks.items():
            for tag in tags:
                # General allergen without explicit profile
                if tag == "allergen":
                    safety_score -= 10
                    safety_issues.append(f"{ingredient}: contains potential allergen ({tag})")
    
    safety_score = max(0, safety_score)
    
    # Sensitivity Score (0-100): Based on sensitivities
    sensitivity_score = 100
    
    # Check PRODUCT INGREDIENTS for match with sensitivities from profile
    for ingredient, tags in ingredient_risks.items():
        ingredient_lower = ingredient.lower()
        matched_from_profile = False
        
        # Check match with avoid_categories (sensitivities)
        for category in avoid_categories_normalized:
            product_keywords = category_mapping.get(category, [category])
            
            # Check risk tags
            for tag in tags:
                tag_lower = tag.lower()
                if any(kw.lower() == tag_lower for kw in product_keywords):
                    if can_say_user_avoids(category, profile):
                        matched_from_profile = True
                        # Penalize for irritants
                        if "fragrance" in tag_lower:
                            sensitivity_score -= 25
                        elif "alcohol" in tag_lower or "drying_alcohol" in tag_lower:
                            sensitivity_score -= 20
                        elif "surfactant" in tag_lower:
                            sensitivity_score -= 20
                        elif "salt" in tag_lower or "high_salt" in tag_lower:
                            sensitivity_score -= 15
                        elif "flavor_enhancer" in tag_lower:
                            sensitivity_score -= 15
                        else:
                            sensitivity_score -= 15
                        
                        sensitivity_issues.append(
                            f"{ingredient}: irritant ({tag}) for your sensitivity ({category})"
                        )
                        from_profile_match.append({
                            "ingredient": ingredient,
                            "tag": tag,
                            "profile_category": category,
                            "type": "sensitivity"
                        })
                        break
            
            # Check ingredient name
            if not matched_from_profile:
                for keyword in product_keywords:
                    key_lower = keyword.lower()
                    if key_lower in ingredient_lower:
                        if can_say_user_avoids(category, profile):
                            matched_from_profile = True
                            if "salt" in key_lower:
                                sensitivity_score -= 15
                            elif "flavor_enhancer" in key_lower:
                                sensitivity_score -= 15
                            else:
                                sensitivity_score -= 15
                            
                            sensitivity_issues.append(
                                f"{ingredient}: ingredient related to sensitivity ({category})"
                            )
                            from_profile_match.append({
                                "ingredient": ingredient,
                                "tag": "ingredient_match",
                                "profile_category": category,
                                "type": "sensitivity"
                            })
                        break
        
        # If didn't match profile but has risks - add to generic_risks and sensitivity_issues
        if not matched_from_profile:
            for tag in tags:
                if tag in ["fragrance", "drying_alcohol", "high_salt", "flavor_enhancer", "harsh_surfactant"]:
                    generic_risks.append({
                        "ingredient": ingredient,
                        "tag": tag,
                        "type": "generic_sensitivity"
                    })
                    sensitivity_issues.append(
                        f"{ingredient}: general irritant ({tag}), even if you didn't indicate it in profile"
                    )
    
    sensitivity_score = max(0, sensitivity_score)
    
    # Match Score (0-100): Based on goals alignment
    match_score = 50  # Start neutral
    
    user_goals = profile.get("goals", [])
    
    # Extract all risk tags if not provided
    if all_risk_tags is None:
        all_risk_tags = []
        for tags in ingredient_risks.values():
            all_risk_tags.extend(tags)
        all_risk_tags = list(set(all_risk_tags))
    
    # Positive matches (beneficial ingredients)
    if "hydrating" in all_risk_tags and any("hydrate" in goal.lower() for goal in user_goals):
        match_score += 20
    if "silicone" in all_risk_tags and any("frizz" in goal.lower() for goal in user_goals):
        match_score += 15
    
    # Negative matches (conflicting ingredients)
    if "drying_alcohol" in all_risk_tags and any("hydrate" in goal.lower() for goal in user_goals):
        match_score -= 20
    if "harsh_surfactant" in all_risk_tags and any("dry" in goal.lower() or "sensitive" in goal.lower() for goal in user_goals):
        match_score -= 15
    
    match_score = max(0, min(100, match_score))
    
    # Aggregate FOR ME Score (weighted average)
    from .scoring_weights import (
        DEFAULT_SAFETY_WEIGHT,
        DEFAULT_SENSITIVITY_WEIGHT,
        DEFAULT_MATCH_WEIGHT,
    )
    for_me_score = int(
        DEFAULT_SAFETY_WEIGHT * safety_score +
        DEFAULT_SENSITIVITY_WEIGHT * sensitivity_score +
        DEFAULT_MATCH_WEIGHT * match_score
    )
    
    # Apply general cap if it was tightened
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
        "reasoning": {
            "safety": f"Safety score: {safety_score}/100 based on allergen matches",
            "sensitivity": f"Sensitivity score: {sensitivity_score}/100 based on irritant matches",
            "match": f"Match score: {match_score}/100 based on goal alignment",
            "final_cap": f"Final score capped at {final_cap} due to allergen penalties"
        }
    }


def calculate_scores_tool(
    profile: Dict[str, Any],
    ingredient_risks: Dict[str, List[str]],
    all_risk_tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Tool wrapper for calculate_scores function.
    
    This function is exposed as a tool to the scoring agent.
    
    Args:
        profile: User profile with allergies, sensitivities, goals
        ingredient_risks: Mapping of ingredient -> risk tags
        all_risk_tags: All unique risk tags found (optional)
    
    Returns:
        Dictionary with scores and reasoning
    """
    if all_risk_tags is None:
        # Extract all unique risk tags from ingredient_risks
        all_risk_tags = []
        for tags in ingredient_risks.values():
            all_risk_tags.extend(tags)
        all_risk_tags = list(set(all_risk_tags))
    
    return calculate_scores(profile, ingredient_risks, all_risk_tags)


def create_scoring_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Creates the Scoring Agent that calculates FOR ME scores.
    
    Args:
        retry_config: HTTP retry configuration
    
    Returns:
        Configured ScoringAgent
    """
    scoring_agent = LlmAgent(
        name="scoring_agent",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        description="Calculates FOR ME compatibility scores (Safety, Sensitivity, Match)",
        instruction="""You are the Scoring Agent for FOR ME.

Your role:
1. Receive user profile and ingredient risk analysis.
2. Call the tool `calculate_scores_tool` to compute:
   - Safety Score (0-100)
   - Sensitivity Score (0-100)
   - Match Score (0-100)
   - FOR ME Score (0-100)
   - Detailed risk_analysis (from_profile_match vs generic_risks)
3. Do NOT recalculate numbers manually. Trust the tool for all numeric scoring.
4. You may rephrase or slightly expand the reasoning text for the final user-facing explanation,
   but the underlying numeric values MUST come from the tool.

Output format:
- Always return a single JSON object with the following keys:
{
  "safety_score": <0-100>,
  "sensitivity_score": <0-100>,
  "match_score": <0-100>,
  "for_me_score": <0-100>,
  "risk_analysis": {
      "from_profile_match": [...],
      "generic_risks": [...]
  },
  "safety_issues": [...],
  "sensitivity_issues": [...],
  "reasoning": {
      "safety": "...",
      "sensitivity": "...",
      "match": "...",
      "final_cap": "..."
  }
}

Rules:
- If the tool returns additional fields (status, final_cap, flags), keep them if helpful.
- Do not invent new scores that are not provided by the tool.
- If the tool indicates severe allergen risk (very low safety or strict_avoid),
  keep the overall FOR ME score low and highlight this clearly in the reasoning.
""",
        tools=[calculate_scores_tool],
        code_executor=BuiltInCodeExecutor(),
    )
    
    return scoring_agent

