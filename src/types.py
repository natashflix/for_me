"""
Type definitions for FOR ME system.

This module provides type aliases and TypedDict classes for better type safety
and code clarity throughout the system.
"""

from typing import Dict, List, Optional, Union, Any, TypedDict
from google.adk.tools.tool_context import ToolContext


# ============================================================================
# Core Type Aliases
# ============================================================================

UserProfile = Dict[str, Any]
"""User profile dictionary containing preferences, allergies, goals, etc."""

IngredientRisks = Dict[str, List[str]]
"""Mapping of ingredient name -> list of risk tags."""

IngredientList = List[str]
"""List of normalized ingredient names."""

RiskTags = List[str]
"""List of risk tags (e.g., ['allergen', 'irritant', 'fragrance'])."""


# ============================================================================
# Score Types
# ============================================================================

class ScoreBreakdown(TypedDict, total=False):
    """Breakdown of individual scores."""
    safety: int  # 0-100
    sensitivity: int  # 0-100
    match: int  # 0-100


class ScoreResult(TypedDict, total=False):
    """Result from scoring functions."""
    status: str  # "success" | "error"
    safety_score: int  # 0-100
    sensitivity_score: int  # 0-100
    match_score: int  # 0-100
    for_me_score: int  # 0-100
    final_cap: int  # Maximum allowed FOR ME score
    has_strict_allergen_explicit: bool
    has_strict_allergen_traces: bool
    risk_analysis: Dict[str, Any]
    safety_issues: List[str]
    sensitivity_issues: List[str]
    category: str  # "food" | "cosmetics" | "household"
    error_message: str  # Only if status == "error"


# ============================================================================
# Agent Response Types
# ============================================================================

class AgentResponse(TypedDict, total=False):
    """Response from agent operations."""
    status: str  # "success" | "error"
    reply: str  # Human-readable response
    for_me_score: Optional[int]  # 0-100, final FOR ME score (only for product analysis)
    intent: str  # "ONBOARDING_REQUIRED" | "PROFILE_UPDATE" | "REACTIONS_AND_PREFERENCES" | "PRODUCT_ANALYSIS" | "SMALL_TALK"
    category: Optional[str]  # "food" | "cosmetics" | "household"
    safety_issues: Optional[List[str]]  # List of safety issues
    sensitivity_issues: Optional[List[str]]  # List of sensitivity issues
    has_strict_allergen_explicit: Optional[bool]  # True if strict allergen found
    has_strict_allergen_traces: Optional[bool]  # True if traces of strict allergen found
    profile: Optional[UserProfile]
    error_message: Optional[str]


# ============================================================================
# Profile Update Types
# ============================================================================

class ProfileUpdate(TypedDict, total=False):
    """Update payload for user profile."""
    food_strict_avoid: List[Union[str, Dict[str, str]]]
    food_prefer_avoid: List[Union[str, Dict[str, str]]]
    food_ok_if_small: List[Union[str, Dict[str, str]]]
    cosmetics_sensitivities: List[str]
    cosmetics_preferences: List[str]
    household_strict_avoid: List[Union[str, Dict[str, str]]]
    household_sensitivities: List[str]
    repeated_negative_reactions: List[Dict[str, Any]]
    hair_type: Optional[str]
    hair_goals: List[str]
    skin_type: Optional[str]
    skin_goals: List[str]
    strict_avoid: List[Union[str, Dict[str, str]]]
    prefer_avoid: List[Union[str, Dict[str, str]]]


# ============================================================================
# Analysis Request Types
# ============================================================================

class AnalysisRequest(TypedDict, total=False):
    """Request for product analysis."""
    user_id: str
    ingredient_text: str
    product_domain: Optional[str]  # "food" | "cosmetics" | "household"
    session_id: Optional[str]
    message: Optional[str]


# ============================================================================
# Context Types
# ============================================================================

class FoodContext(TypedDict, total=False):
    """Structured context for food product analysis."""
    profile: Dict[str, Any]
    ingredients: IngredientList
    ingredient_risks: IngredientRisks
    dictionaries: Dict[str, Dict[str, List[str]]]


class CosmeticsContext(TypedDict, total=False):
    """Structured context for cosmetics product analysis."""
    profile: Dict[str, Any]
    ingredients: IngredientList
    ingredient_risks: IngredientRisks
    dictionaries: Dict[str, Dict[str, List[str]]]


class HouseholdContext(TypedDict, total=False):
    """Structured context for household product analysis."""
    profile: Dict[str, Any]
    ingredients: IngredientList
    ingredient_risks: IngredientRisks
    dictionaries: Dict[str, Dict[str, List[str]]]


# ============================================================================
# Tool Result Types
# ============================================================================

class ParseIngredientsResult(TypedDict, total=False):
    """Result from parse_ingredients tool."""
    status: str  # "success" | "error"
    ingredients: List[str]
    count: int
    error_message: str  # Only if status == "error"


class RiskDictionaryResult(TypedDict, total=False):
    """Result from get_ingredient_risks tool."""
    status: str  # "success" | "error"
    risks: IngredientRisks
    all_risk_tags: List[str]
    ingredients_with_risks: int
    total_ingredients: int
    error_message: str  # Only if status == "error"


# ============================================================================
# Repeated Reaction Types
# ============================================================================

class RepeatedReaction(TypedDict, total=False):
    """Entry for repeated negative reaction."""
    ingredient: str
    reaction: str
    frequency: str  # "always" | "often" | "sometimes" | etc.
    domain: Optional[str]  # "food" | "cosmetics" | "household"
    reported_at: Optional[str]  # ISO timestamp


# ============================================================================
# Function Signatures (for type checking)
# ============================================================================

def analyze_product_signature(
    user_id: str,
    ingredient_text: str,
    product_domain: Optional[str] = None,
    session_id: Optional[str] = None,
    skip_onboarding: bool = False,
) -> AgentResponse:
    """Type signature for analyze_product function."""
    ...


def handle_chat_request_signature(
    user_id: str,
    message: Optional[str] = None,
    ingredient_text: Optional[str] = None,
    product_domain: Optional[str] = None,
    session_id: Optional[str] = None,
) -> AgentResponse:
    """Type signature for handle_chat_request function."""
    ...


def calculate_scores_signature(
    profile: UserProfile,
    ingredient_risks: IngredientRisks,
    all_risk_tags: Optional[RiskTags] = None,
) -> ScoreResult:
    """Type signature for calculate_scores function."""
    ...


def update_long_term_profile_signature(
    tool_context: ToolContext,
    user_id: str,
    updates: ProfileUpdate,
) -> UserProfile:
    """Type signature for update_long_term_profile function."""
    ...

