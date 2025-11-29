"""
Memory Design for FOR ME System

Implements explicit separation between:
- Long-term memory: Persistent user profile, preferences, and health observations
- Short-term memory: Session-scoped temporary data (not persisted)

CRITICAL:
- Long-term memory is stored in user_profile and reused across all sessions
- Short-term memory is NOT stored in long-term memory
- Health information = user-reported experience, NOT medical data
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime
import copy
from google.adk.tools.tool_context import ToolContext

if TYPE_CHECKING:
    from .types import UserProfile, ProfileUpdate, RepeatedReaction
else:
    # Runtime fallback to avoid circular imports
    UserProfile = Dict[str, Any]
    ProfileUpdate = Dict[str, Any]
    RepeatedReaction = Dict[str, Any]


# ============================================================================
# LONG-TERM MEMORY STRUCTURE
# ============================================================================

LONG_TERM_PROFILE_STRUCTURE = {
    # Stable personal constraints (persist across sessions)
    "food_strict_avoid": [],  # Allergies, religious restrictions, ethical bans
    "food_prefer_avoid": [],  # Sugar, ultra-processed ingredients
    "food_ok_if_small": [],  # OK in small amounts
    "cosmetics_sensitivities": [],  # SLS, fragrance, alcohol
    "cosmetics_preferences": [],  # Preferred ingredients
    "household_strict_avoid": [],  # Chlorine, strong solvents
    "household_sensitivities": [],  # Irritants
    
    # Stable user-reported health observations
    "repeated_negative_reactions": [],  # Format: [{"ingredient": "...", "reaction": "...", "frequency": "..."}]
    
    # Hair and skin characteristics
    "hair_type": None,  # "curly", "straight", "dry", "oily"
    "hair_goals": [],  # ["hydration", "anti_frizz", "curl_definition"]
    "skin_type": None,  # "dry", "oily", "sensitive", "combination"
    "skin_goals": [],  # ["hydration", "anti_aging", "acne_control"]
    
    # Metadata
    "created_at": None,
    "updated_at": None,
    "version": 1,
}

# Default empty profile (for initialization)
DEFAULT_EMPTY_PROFILE = {
    "food_strict_avoid": [],
    "food_prefer_avoid": [],
    "food_ok_if_small": [],
    "cosmetics_sensitivities": [],
    "cosmetics_preferences": [],
    "household_strict_avoid": [],
    "household_sensitivities": [],
    "repeated_negative_reactions": [],
    "hair_type": None,
    "hair_goals": [],
    "skin_type": None,
    "skin_goals": [],
}


# ============================================================================
# SHORT-TERM MEMORY STRUCTURE
# ============================================================================

SHORT_TERM_CONTEXT_STRUCTURE = {
    # Session-scoped data (NOT stored in long-term memory)
    "current_product_name": None,
    "current_ingredient_list": [],
    "current_category": None,
    "temporary_clarifications": [],  # User clarifications during analysis
    "session_id": None,
    "created_at": None,
}


# ============================================================================
# MEMORY MANAGEMENT FUNCTIONS
# ============================================================================

def is_profile_minimal(profile: Dict[str, Any]) -> bool:
    """
    Checks if profile is missing or too minimal to be useful.
    
    A profile is considered minimal if:
    - It doesn't exist (empty dict)
    - It has no meaningful data (all fields are None/empty)
    - It's missing critical fields (hair_type, skin_type, any avoid lists)
    
    Args:
        profile: User profile dictionary
    
    Returns:
        True if profile is minimal/empty, False otherwise
    """
    if not profile:
        return True
    
    # Check if profile has any meaningful data
    meaningful_fields = [
        "hair_type",
        "skin_type",
        "food_strict_avoid",
        "food_prefer_avoid",
        "cosmetics_sensitivities",
        "household_strict_avoid",
    ]
    
    # Add additional meaningful fields for completeness
    meaningful_fields.extend([
        "hair_goals",
        "skin_goals",
        "repeated_negative_reactions"
    ])
    
    has_data = False
    for field in meaningful_fields:
        value = profile.get(field)
        if value:
            if isinstance(value, list) and len(value) > 0:
                has_data = True
                break
            elif isinstance(value, str) and value.strip():
                has_data = True
                break
    
    return not has_data


def get_long_term_profile(tool_context: ToolContext, user_id: str) -> UserProfile:
    """
    Retrieves long-term profile from memory.
    
    Long-term memory contains:
    - Stable personal constraints (food_strict_avoid, cosmetics_sensitivities, etc.)
    - Repeated negative reactions
    - Hair/skin characteristics
    
    This data persists across all sessions and directly affects scores.
    """
    profile_key = f"user:{user_id}:long_profile"
    profile = tool_context.state.get(profile_key)
    
    if not profile:
        # Initialize with default structure
        profile = copy.deepcopy(LONG_TERM_PROFILE_STRUCTURE)
        profile["created_at"] = datetime.now().isoformat()
        profile["updated_at"] = datetime.now().isoformat()
        tool_context.state[profile_key] = profile
    
    return profile


def _ensure_list(value):
    """Helper to ensure value is a list (handles LLM errors where string is passed instead of list)."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def update_long_term_profile(
    tool_context: ToolContext,
    user_id: str,
    updates: ProfileUpdate,
) -> UserProfile:
    """
    Updates long-term profile with new information.
    
    Only updates stable constraints and health observations.
    Does NOT store ingredient lists or product history.
    
    Args:
        tool_context: ADK tool context
        user_id: User identifier
        updates: Dictionary with fields to update
    
    Returns:
        Updated profile
    """
    profile = get_long_term_profile(tool_context, user_id)
    
    # Update allowed fields
    allowed_fields = [
        "food_strict_avoid",
        "food_prefer_avoid",
        "food_ok_if_small",
        "cosmetics_sensitivities",
        "cosmetics_preferences",
        "household_strict_avoid",
        "household_sensitivities",
        "repeated_negative_reactions",
        "hair_type",
        "hair_goals",
        "skin_type",
        "skin_goals",
    ]
    
    # List fields that should always be lists
    list_fields = [
        "food_strict_avoid",
        "food_prefer_avoid",
        "food_ok_if_small",
        "cosmetics_sensitivities",
        "cosmetics_preferences",
        "household_strict_avoid",
        "household_sensitivities",
        "hair_goals",
        "skin_goals",
    ]
    
    for field, value in updates.items():
        if field in allowed_fields:
            if field == "repeated_negative_reactions":
                # Append to list, don't replace
                if field not in profile:
                    profile[field] = []
                if isinstance(value, list):
                    profile[field].extend(value)
                else:
                    profile[field].append(value)
            elif field in list_fields:
                # Ensure list type for list fields
                profile[field] = _ensure_list(value)
            else:
                # Non-list fields (hair_type, skin_type)
                profile[field] = value
    
    profile["updated_at"] = datetime.now().isoformat()
    profile["version"] = profile.get("version", 1) + 1
    
    # Save back to state
    profile_key = f"user:{user_id}:long_profile"
    tool_context.state[profile_key] = profile
    
    return profile


def add_repeated_negative_reaction(
    tool_context: ToolContext,
    user_id: str,
    ingredient: str,
    reaction: str,
    frequency: str = "always",
) -> UserProfile:
    """
    Adds a repeated negative reaction to long-term memory.
    
    Example:
        "this shampoo causes scalp itching every time"
        "I always get bloating from milk chocolate"
    
    This information directly affects Safety Score and FOR ME Score caps.
    """
    reaction_entry = {
        "ingredient": ingredient,
        "reaction": reaction,
        "frequency": frequency,
        "reported_at": datetime.now().isoformat(),
    }
    
    return update_long_term_profile(
        tool_context=tool_context,
        user_id=user_id,
        updates={"repeated_negative_reactions": [reaction_entry]},
    )


def get_short_term_context(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Retrieves short-term context for current session.
    
    Short-term memory contains:
    - Current product name
    - Current ingredient list
    - Temporary clarifications
    
    This data is session-scoped and NOT stored in long-term memory.
    """
    context = tool_context.state.get("short_term_context", {})
    
    if not context:
        context = copy.deepcopy(SHORT_TERM_CONTEXT_STRUCTURE)
        context["created_at"] = datetime.now().isoformat()
        tool_context.state["short_term_context"] = context
    
    return context


def update_short_term_context(
    tool_context: ToolContext,
    product_name: Optional[str] = None,
    ingredient_list: Optional[List[str]] = None,
    category: Optional[str] = None,
    clarification: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates short-term context for current session.
    
    This data is NOT persisted to long-term memory.
    """
    context = get_short_term_context(tool_context)
    
    if product_name is not None:
        context["current_product_name"] = product_name
    if ingredient_list is not None:
        context["current_ingredient_list"] = ingredient_list
    if category is not None:
        context["current_category"] = category
    if clarification is not None:
        if "temporary_clarifications" not in context:
            context["temporary_clarifications"] = []
        context["temporary_clarifications"].append({
            "text": clarification,
            "timestamp": datetime.now().isoformat(),
        })
    if session_id is not None:
        context["session_id"] = session_id
    
    context["updated_at"] = datetime.now().isoformat()
    tool_context.state["short_term_context"] = context
    return context


def clear_short_term_context(tool_context: ToolContext) -> None:
    """
    Clears short-term context (called at end of session).
    
    Short-term memory is NOT stored in long-term memory.
    """
    tool_context.state["short_term_context"] = copy.deepcopy(SHORT_TERM_CONTEXT_STRUCTURE)


def apply_repeated_reactions_to_scores(
    profile: UserProfile,
    ingredients_list: List[str],
    current_safety_score: int,
    current_final_cap: int,
) -> tuple[int, int]:
    """
    Applies repeated negative reactions from long-term memory to scores.
    
    If an ingredient in the product has been reported as causing
    repeated negative reactions, it affects Safety Score and final_cap.
    
    This function directly influences scoring based on user-reported
    health observations stored in long-term memory.
    
    Args:
        profile: User profile containing repeated_negative_reactions
        ingredients_list: List of normalized ingredient names from product
        current_safety_score: Current safety score before applying reactions
        current_final_cap: Current final cap before applying reactions
    
    Returns:
        Tuple of (updated_safety_score, updated_final_cap)
    """
    repeated_reactions = profile.get("repeated_negative_reactions", [])
    
    for ingredient in ingredients_list:
        ingredient_lower = ingredient.lower()
        
        for reaction_entry in repeated_reactions:
            reaction_ingredient = reaction_entry.get("ingredient", "").lower()
            frequency = reaction_entry.get("frequency", "always")
            
            if reaction_ingredient in ingredient_lower or ingredient_lower in reaction_ingredient:
                # Repeated negative reaction detected
                freq = frequency.lower().strip()
                
                severe_triggers = ["always", "every time", "consistently", "constant", "regularly"]
                moderate_triggers = ["often", "frequently", "usually", "many times"]
                mild_triggers = ["sometimes", "occasionally", "rarely"]
                
                if freq in severe_triggers:
                    # Severe: Safety = 0, cap = 10
                    current_safety_score = 0
                    current_final_cap = min(current_final_cap, 10)
                elif freq in moderate_triggers:
                    # Moderate: Safety reduced, cap = 20
                    current_safety_score = min(current_safety_score, 20)
                    current_final_cap = min(current_final_cap, 20)
                elif freq in mild_triggers:
                    # Mild: Small penalty
                    current_safety_score = max(0, current_safety_score - 30)
                    current_final_cap = min(current_final_cap, 50)
                else:
                    # Unknown frequency: treat as moderate
                    current_safety_score = min(current_safety_score, 20)
                    current_final_cap = min(current_final_cap, 20)
    
    return current_safety_score, current_final_cap


# ============================================================================
# DISCLAIMER
# ============================================================================

DISCLAIMER = (
    "FOR ME Score reflects compatibility with your preferences and sensitivities "
    "based on user-provided data, not medical advice."
)

