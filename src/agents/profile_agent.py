"""
Profile Agent

Manages user profiles using Memory Bank.
"""

from typing import Dict, Any
from copy import deepcopy
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
from google.genai import types


DEFAULT_LONG_TERM_PROFILE = {
    # High-level notes and goals
    "health_notes": [],
    "avoid_categories": [],       # e.g. ["dairy", "gluten", "high_salt", "fragrance"]
    "avoid_ingredients": [],      # e.g. ["yellow-5", "SLS", "almonds"]
    "goals": [],                  # e.g. ["hydrate_skin", "reduce_bloating"]
    "learned_patterns": [],       # e.g. ["reacts_negatively_to_SLS"]

    # New fields for strictness levels (global)
    "strict_avoid": [],           # Strict avoidance (allergens) - [{"ingredient": "...", "type": "allergen"}, ...]
    "prefer_avoid": [],           # Preference to avoid - [{"ingredient": "...", "type": "preference"}, ...]

    # Category-specific fields for logic separation
    "food_strict_avoid": [],      # Strict avoidance for food
    "food_prefer_avoid": [],      # Preference to avoid for food
    "food_ok_if_small": [],       # OK if in small quantities (food only)

    "cosmetics_sensitivities": [],    # Sensitivities for cosmetics (e.g. ["fragrance", "drying_alcohol"])
    "cosmetics_preferences": [],      # Preferences for cosmetics (e.g. ["silicone_free"])

    "household_strict_avoid": [],     # Strict avoidance for household products (e.g. ["bleach", "ammonia"])
    "household_sensitivities": [],    # Sensitivities for household products

    # Cosmetics-specific profile
    "hair_type": None,            # "curly", "straight", "wavy", etc.
    "hair_goals": [],             # ["hydration", "anti_frizz", "curl_definition", ...]

    "skin_type": None,            # "dry", "oily", "sensitive", "combination", etc.
    "skin_goals": [],             # ["hydration", "anti_aging", "acne_control", ...]

    # Long-term negative reactions learned over time
    "repeated_negative_reactions": [],  # e.g. [{"ingredient": "...", "domain": "food" | "cosmetics" | "household"}]

    # Backwards compatibility fields (legacy structure)
    "allergies": [],
    "sensitivities": [],
}


def _ensure_long_term_profile(tool_context: ToolContext, user_id: str) -> Dict[str, Any]:
    """Returns existing long-term profile or initializes a default one."""
    profile_key = f"user:{user_id}:long_profile"
    profile = tool_context.state.get(profile_key)

    if profile:
        return profile

    # Initialize default profile on first onboarding
    tool_context.state[profile_key] = deepcopy(DEFAULT_LONG_TERM_PROFILE)
    return tool_context.state[profile_key]


def load_user_profile(tool_context: ToolContext, user_id: str) -> Dict[str, Any]:
    """
    Loads user profile from Memory Bank (session state in MVP).
    
    In production, this would query Vertex AI Memory Bank.
    For MVP, we use session state as a simple memory store.
    
    Args:
        tool_context: ADK tool context with access to state
        user_id: User identifier
    
    Returns:
        Dictionary with profile data or default profile
    """
    # Check session state for user profile
    profile = _ensure_long_term_profile(tool_context, user_id)
    short_term_context = tool_context.state.get("short_term_context", {})

    return {
        "status": "success",
        "profile": profile,
        "short_term_context": short_term_context,
        "source": "memory"
    }


def save_long_term_profile(
    tool_context: ToolContext,
    user_id: str,
    health_notes: list | None = None,
    avoid_categories: list | None = None,
    avoid_ingredients: list | None = None,
    goals: list | None = None,
    learned_patterns: list | None = None,
    strict_avoid: list | None = None,
    prefer_avoid: list | None = None,
    # Category-specific fields
    food_strict_avoid: list | None = None,
    food_prefer_avoid: list | None = None,
    food_ok_if_small: list | None = None,
    cosmetics_sensitivities: list | None = None,
    cosmetics_preferences: list | None = None,
    household_strict_avoid: list | None = None,
    household_sensitivities: list | None = None,
    hair_type: str | None = None,
    hair_goals: list | None = None,
    skin_type: str | None = None,
    skin_goals: list | None = None,
    repeated_negative_reactions: list | None = None,
    allergies: list | None = None,
    sensitivities: list | None = None,
) -> Dict[str, Any]:
    """
    Saves long-term profile (onboarding data).
    """
    current_profile = _ensure_long_term_profile(tool_context, user_id)
    
    # Update fields if provided
    if health_notes is not None:
        current_profile["health_notes"] = health_notes
    if avoid_categories is not None:
        current_profile["avoid_categories"] = avoid_categories
    if avoid_ingredients is not None:
        current_profile["avoid_ingredients"] = avoid_ingredients
    if goals is not None:
        current_profile["goals"] = goals
    if learned_patterns is not None:
        current_profile["learned_patterns"] = learned_patterns
    if strict_avoid is not None:
        current_profile["strict_avoid"] = strict_avoid
    if prefer_avoid is not None:
        current_profile["prefer_avoid"] = prefer_avoid
    # Category-specific fields
    if food_strict_avoid is not None:
        current_profile["food_strict_avoid"] = food_strict_avoid
    if food_prefer_avoid is not None:
        current_profile["food_prefer_avoid"] = food_prefer_avoid
    if food_ok_if_small is not None:
        current_profile["food_ok_if_small"] = food_ok_if_small
    if cosmetics_sensitivities is not None:
        current_profile["cosmetics_sensitivities"] = cosmetics_sensitivities
    if cosmetics_preferences is not None:
        current_profile["cosmetics_preferences"] = cosmetics_preferences
    if household_strict_avoid is not None:
        current_profile["household_strict_avoid"] = household_strict_avoid
    if household_sensitivities is not None:
        current_profile["household_sensitivities"] = household_sensitivities
    if hair_type is not None:
        current_profile["hair_type"] = hair_type
    if hair_goals is not None:
        current_profile["hair_goals"] = hair_goals
    if skin_type is not None:
        current_profile["skin_type"] = skin_type
    if skin_goals is not None:
        current_profile["skin_goals"] = skin_goals
    if repeated_negative_reactions is not None:
        current_profile["repeated_negative_reactions"] = repeated_negative_reactions
    
    # Backward compatibility: convert old fields
    if allergies is not None:
        current_profile["allergies"] = allergies
        # Convert to new structure
        if not current_profile.get("avoid_ingredients"):
            current_profile["avoid_ingredients"] = allergies
    if sensitivities is not None:
        current_profile["sensitivities"] = sensitivities
        # Convert to new structure
        if not current_profile.get("avoid_categories"):
            current_profile["avoid_categories"] = sensitivities
    
    profile_key = f"user:{user_id}:long_profile"
    tool_context.state[profile_key] = current_profile
    
    return {
        "status": "success",
        "profile": current_profile
    }


def load_long_term_profile(tool_context: ToolContext, user_id: str) -> Dict[str, Any]:
    """Explicit tool to load long-term profile."""
    profile = _ensure_long_term_profile(tool_context, user_id)
    return {
        "status": "success",
        "profile": profile
    }


def save_user_profile(
    tool_context: ToolContext,
    user_id: str,
    **kwargs,
) -> Dict[str, Any]:
    """Backward compatible wrapper."""
    return save_long_term_profile(tool_context, user_id, **kwargs)


def load_short_term_context(tool_context: ToolContext) -> Dict[str, Any]:
    """Returns short-term context stored in the current session."""
    context = tool_context.state.get("short_term_context", {})
    return {
        "status": "success",
        "context": context
    }


def save_short_term_context(
    tool_context: ToolContext,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Saves short-term context (e.g., latest recipe info) in session state."""
    tool_context.state["short_term_context"] = context
    return {
        "status": "success",
        "context": context
    }


def create_profile_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Creates the Profile Agent that manages user profiles.

    Args:
        retry_config: HTTP retry configuration

    Returns:
        Configured ProfileAgent
    """
    profile_agent = LlmAgent(
        name="profile_agent",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        description="Manages user profiles and preferences using long-term and short-term memory for the FOR ME system.",
        instruction="""You are the Profile Agent for FOR ME.

Your responsibilities:
1. Load user profiles using the `load_user_profile` tool.
2. Save/update user profiles using the `save_user_profile` tool.
3. Return profile data in a clean, structured JSON format for other agents.

HOW TO BEHAVE:
- Always call `load_user_profile` first to get the current profile.
- If fields are missing, assume the default profile structure.
- When saving, only update the fields explicitly provided to you.
- Do NOT invent new schema fields – use the existing structure.

PROFILE STRUCTURE (KEY FIELDS):

High-level:
- health_notes: list[str]
- avoid_categories: list[str]        # e.g. ["dairy", "gluten", "high_salt", "fragrance"]
- avoid_ingredients: list[str]       # e.g. ["yellow-5", "SLS", "almonds"]
- goals: list[str]                   # e.g. ["hydrate_skin", "reduce_bloating"]
- learned_patterns: list[str]        # e.g. ["reacts_negatively_to_SLS"]

Strictness levels (global):
- strict_avoid: list[{"ingredient": str, "type": "allergen"}]
- prefer_avoid: list[{"ingredient": str, "type": "preference"}]

Food-specific:
- food_strict_avoid: list[str or dict]
- food_prefer_avoid: list[str or dict]
- food_ok_if_small: list[str or dict]

Cosmetics-specific:
- cosmetics_sensitivities: list[str]     # e.g. ["fragrance", "drying_alcohol"]
- cosmetics_preferences: list[str]       # e.g. ["silicone_free"]
- hair_type: str or null                 # "curly", "straight", "wavy", etc.
- hair_goals: list[str]                  # ["hydration", "anti_frizz", "curl_definition", ...]
- skin_type: str or null                 # "dry", "oily", "sensitive", "combination", etc.
- skin_goals: list[str]                  # ["hydration", "anti_aging", "acne_control", ...]

Household-specific:
- household_strict_avoid: list[str or dict]
- household_sensitivities: list[str]

Long-term reactions:
- repeated_negative_reactions: list[dict]
  # e.g. [{"ingredient": "SLS", "domain": "cosmetics"}]

Backward compatibility (legacy fields):
- allergies: list[str]
- sensitivities: list[str]

OUTPUT:
- When responding, return JSON like:
  {
    "status": "success",
    "profile": { ... },          # full profile following the structure above
    "short_term_context": {...}, # optional, if available
    "source": "memory"
  }

- Do NOT provide medical interpretations.
- Do NOT add diagnoses or health claims.
- Your job is purely to manage structured preference data.
""",
        tools=[load_user_profile, save_user_profile],
    )

    return profile_agent

