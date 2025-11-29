"""
Router Agent

Main orchestrator that determines product category and routes to appropriate
compatibility agent using A2A (agent-as-a-tool) pattern.

The RouterAgent does not contain domain logic itself. It delegates to
specialized agents via clear, typed method calls.
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

from ..tools import parse_ingredients
from .profile_agent import (
    load_user_profile,
    load_long_term_profile,
    load_short_term_context,
    save_long_term_profile,
    save_short_term_context,
)
from .category_tools import (
    detect_product_category,
    analyze_food_product,
    analyze_cosmetics_product,
    analyze_household_product,
)
from .profile_update_agent import create_profile_update_agent
from .explainer_agent import create_explainer_agent


def create_router_agent(
    retry_config: types.HttpRetryOptions,
    include_profile_agent: bool = True,
    include_explainer_agent: bool = True,
) -> LlmAgent:
    """
    Creates the Router Agent that orchestrates the multi-agent pipeline.
    
    The RouterAgent acts as the primary orchestrator using an A2A-style,
    agent-as-a-tool pattern to invoke specialized agents:
    - It calls ProfileAgent to load the user's long-term profile
    - It delegates compatibility reasoning to Category Agents (Food, Cosmetics, Household)
    - It optionally calls ProfileUpdateAgent to update long-term memory
    - It calls ExplainerAgent to synthesize user-facing explanations
    
    Args:
        retry_config: HTTP retry configuration
        include_profile_agent: Whether to include ProfileUpdateAgent in tools
        include_explainer_agent: Whether to include ExplainerAgent in tools
    
    Returns:
        Configured RouterAgent
    """
    router_agent = LlmAgent(
        name="router_agent",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        description="Entry point that detects product category and routes to category-specific compatibility agent",
        instruction="""You are the Router Agent for FOR ME - a personalized product compatibility system.

CRITICAL: Strict category separation!

1. CATEGORY DETECTION:
   Use detect_product_category to determine product category:
   - "food" → FoodCompatibilityAgent (STRICT logic)
   - "cosmetics" → CosmeticsCompatibilityAgent (SOFT logic)
   - "household" → HouseholdCompatibilityAgent (MEDIUM logic)

2. ROUTING (A2A Pattern):
   After determining category, call the corresponding agent as a tool:
   
   if category == "food":
       → analyze_food_product(user_id, ingredient_text)
   elif category == "cosmetics":
       → analyze_cosmetics_product(user_id, ingredient_text)
   elif category == "household":
       → analyze_household_product(user_id, ingredient_text)

3. RESULT FORMATTING:
   
   🎯 FOR ME Score: X/100
      (interpretation based on category and profile)
   
   📊 Details:
      Safety Score: X/100
      Sensitivity Score: X/100
      Match Score: X/100
   
   ⚠️ Detected issues (only from profile)
   ✅ Positive aspects (if any)
   
   ℹ️ Important: This score is based on data you provided in your profile.
      It is not a medical conclusion.

4. CRITICAL RULES:
   - NEVER mix category logic
   - NEVER use words: "allergy", "diagnosis", "medical"
   - ALWAYS use: "you indicated in your profile", "you marked"
   - For food: be strict with allergens
   - For cosmetics: be soft, don't scare the user
   - For household: medium strictness

5. SEQUENCE (Multi-Agent Orchestration):
   a. detect_product_category - determine category
   b. load_user_profile - load profile from long-term memory
   c. (Optional) ProfileUpdateAgent - check if profile needs update
   d. Call corresponding analyze_*_product agent
   e. (Optional) ExplainerAgent - transform result to user-friendly explanation
   f. Form final response with disclaimer

6. A2A AGENTS (if enabled):
   - ProfileUpdateAgent: analyzes user statements about reactions
   - ExplainerAgent: generates user-friendly explanation

Important: Each category works independently. Do not mix!
""",
        tools=[
            load_user_profile,
            load_long_term_profile,
            parse_ingredients,
            detect_product_category,
            analyze_food_product,
            analyze_cosmetics_product,
            analyze_household_product,
        ],
    )
    
    return router_agent
