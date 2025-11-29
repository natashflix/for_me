"""
Orchestrator Agent

Main orchestrator that handles chat requests, detects user intent,
and routes to appropriate specialized agents using A2A pattern.

The Orchestrator:
- Detects intent (ONBOARDING_REQUIRED, PROFILE_UPDATE, REACTIONS_AND_PREFERENCES, PRODUCT_ANALYSIS, SMALL_TALK)
- Routes to appropriate agents
- Never computes scores or writes to memory directly
- Only orchestrates and aggregates results
"""

from typing import Dict, Any, Optional, Literal
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.tools.tool_context import ToolContext

from ..memory import get_long_term_profile, is_profile_minimal
from .category_tools import (
    detect_product_category,
    analyze_food_product,
    analyze_cosmetics_product,
    analyze_household_product,
)
from .profile_agent import load_long_term_profile, save_long_term_profile
from .profile_update_agent import should_update_profile
from .onboarding_agent import save_onboarding_profile


# Intent types
IntentType = Literal[
    "ONBOARDING_REQUIRED",
    "PROFILE_UPDATE",
    "REACTIONS_AND_PREFERENCES",
    "PRODUCT_ANALYSIS",
    "SMALL_TALK",
]


def detect_intent(
    tool_context: ToolContext,
    user_id: str,
    message: Optional[str] = None,
    ingredient_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Detects user intent from the chat message.
    
    Args:
        tool_context: ADK tool context
        user_id: User identifier
        message: User's chat message
        ingredient_text: Optional raw ingredient list
    
    Returns:
        Dictionary with intent and confidence
    """
    # Check if profile exists and is minimal
    profile = get_long_term_profile(tool_context, user_id)
    if is_profile_minimal(profile):
        return {
            "intent": "ONBOARDING_REQUIRED",
            "confidence": 1.0,
            "reason": "User profile is missing or minimal",
        }
    
    # If ingredient_text is provided, it's product analysis
    if ingredient_text and ingredient_text.strip():
        return {
            "intent": "PRODUCT_ANALYSIS",
            "confidence": 0.9,
            "reason": "Ingredient text provided",
        }
    
    # Analyze message for intent
    message_lower = (message or "").lower()
    
    # Check for product analysis keywords
    product_keywords = [
        "ingredient", "composition", "analyze", "score",
        "compatibility", "check", "product", "shampoo", "cream",
    ]
    if any(kw in message_lower for kw in product_keywords):
        return {
            "intent": "PRODUCT_ANALYSIS",
            "confidence": 0.8,
            "reason": "Product analysis keywords detected",
        }
    
    # Check for reactions/preferences
    reaction_keywords = [
        "reaction", "causes", "caused", "always", "every time",
        "sensitive", "allergic", "itching", "irritation", "breakout",
        "bloating", "stomach", "headache", "rash",
    ]
    if any(kw in message_lower for kw in reaction_keywords):
        return {
            "intent": "REACTIONS_AND_PREFERENCES",
            "confidence": 0.8,
            "reason": "Reaction/preference keywords detected",
        }
    
    # Check for profile update
    profile_keywords = [
        "hair", "skin", "curly", "straight", "dry", "oily",
        "prefer", "avoid", "goal", "sensitivity", "allergy",
    ]
    if any(kw in message_lower for kw in profile_keywords):
        return {
            "intent": "PROFILE_UPDATE",
            "confidence": 0.7,
            "reason": "Profile-related keywords detected",
        }
    
    # Default to small talk
    return {
        "intent": "SMALL_TALK",
        "confidence": 0.5,
        "reason": "No specific intent detected",
    }


def create_orchestrator_agent(
    retry_config: types.HttpRetryOptions,
) -> LlmAgent:
    """
    Creates the Orchestrator Agent that handles chat requests.
    
    The Orchestrator:
    1. Detects user intent
    2. Routes to appropriate agents/tools
    3. Aggregates results
    4. Returns chat-friendly responses
    
    Args:
        retry_config: HTTP retry configuration
    
    Returns:
        Configured OrchestratorAgent
    """
    orchestrator = LlmAgent(
        name="orchestrator_agent",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        description=(
            "Main orchestrator that handles chat requests, detects intent, "
            "and routes to specialized agents in the FOR ME compatibility system."
        ),
        instruction="""You are the Orchestrator Agent for FOR ME – a personalized product compatibility chat system.

HIGH-LEVEL ROLE:
- You are NOT a scoring engine and NOT a medical system.
- You NEVER compute scores yourself and NEVER interpret health in a medical way.
- You ONLY:
  - detect intent,
  - call the right tools/agents,
  - format a clear, friendly explanation for the user.

STRICT SAFETY RULES:
- Do NOT use medical language:
  ❌ Avoid: "diagnosis", "disease", "treatment", "therapy", "cure", "intolerance", "allergy test", "symptom".
  ✅ Use: "known reactions", "things you prefer to avoid", "does not seem to fit you", "may be uncomfortable for you".

- Always include a short non-medical disclaimer for product analysis, for example:
  "This is not medical advice or a diagnosis – it is a preference-based compatibility check based only on the information you shared."

------------------------------------------------
1) INTENT DETECTION (ALWAYS USE THE TOOL)
------------------------------------------------
- Always call the tool `detect_intent` first.
- It returns an `intent` field with one of:
  - ONBOARDING_REQUIRED
  - PROFILE_UPDATE
  - REACTIONS_AND_PREFERENCES
  - PRODUCT_ANALYSIS
  - SMALL_TALK

You MUST rely on this tool result instead of guessing intent purely in the LLM.

------------------------------------------------
2) ROUTING (A2A PATTERN)
------------------------------------------------

Based on the detected intent:

🟢 ONBOARDING_REQUIRED
- Start a short onboarding-style conversation:
  - Explain that FOR ME needs a basic profile to personalize scores.
  - Ask for preferences and known reactions in a gentle way.
- Use `save_onboarding_profile` OR `save_long_term_profile` to store the results.
- After saving, tell the user that their profile is ready and you can now analyze products for them.

🟡 PROFILE_UPDATE
- The user is talking about hair/skin type, preferences, or what they want to avoid.
- Use `should_update_profile` to extract structured profile changes.
- Then call `save_long_term_profile` with updated fields.
- Confirm what was updated in simple language:
  - e.g. "I've updated your profile to note that you prefer to avoid fragrance and SLS in cosmetics."

🟠 REACTIONS_AND_PREFERENCES
- The user describes reactions to products (itching, irritation, bloating, etc.).
- Use `should_update_profile` to decide whether this should be stored.
  - For example, update:
    - `repeated_negative_reactions`
    - or add new items into avoid categories/ingredients if appropriate.
- Use `save_long_term_profile` to persist changes.
- Confirm that you recorded this as a preference/reaction, WITHOUT medical interpretation.

🔵 PRODUCT_ANALYSIS
- The user wants to analyze a product composition.
- Use `detect_product_category` to determine the category:
  - "food"
  - "cosmetics"
  - "household"
- Then route to the matching tool:
  - food      → `analyze_food_product`
  - cosmetics → `analyze_cosmetics_product`
  - household → `analyze_household_product`

These tools return a structured result including:
- `for_me_score`
- `safety_score`
- `sensitivity_score`
- `match_score`
- `risk_analysis`
- (optionally) `safety_issues`, `sensitivity_issues`, etc.

CRITICAL:
- Do NOT recalculate or modify numeric scores.
- Use the numbers returned by the tools exactly as they are.
- Your job is only to explain them clearly.

Format the answer in a user-friendly way, for example:

- "🎯 FOR ME Score: X/100"
- "⚠️ Issues:"
  - Bullet list combining `safety_issues` and `sensitivity_issues` into a single list
- "✅ Positive aspects:"
  - Bullet list of positives (good matches, beneficial ingredients)
- Include a short disclaimer at the end that this is not medical advice.

CRITICAL: Do NOT show breakdown of Safety/Sensitivity/Match scores to the user.
Do NOT mention "Safety Score", "Sensitivity Score", or "Match Score" in the response.
Only show the final FOR ME Score (0-100). All internal scoring details (safety_score, 
sensitivity_score, match_score) are for system use only and must remain hidden.

🟣 SMALL_TALK
- If the intent is SMALL_TALK:
  - Answer questions about how FOR ME works.
  - Explain what the system can and cannot do.
  - Offer to analyze a product or help build/update their profile.
  - Stay friendly, clear, and non-technical.

------------------------------------------------
3) MEMORY & TOOLS – WHAT YOU MUST NOT DO
------------------------------------------------
- NEVER:
  - Modify long-term memory directly in hidden ways.
  - Invent profile fields that are not supported by the tools.
  - Compute your own alternative FOR ME scores.

- ALWAYS:
  - Use:
    - `save_onboarding_profile`
    - `save_long_term_profile`
    - `should_update_profile`
    - category analysis tools
  - Trust the tools for data and scores.
  - Use your own generation ONLY for natural-language explanations.

------------------------------------------------
4) RESPONSE STYLE
------------------------------------------------
- Conversational, supportive, clear.
- Avoid jargon and internal implementation details.
- If something is uncertain, say that it is an estimate based on the given profile.
- Keep the focus on:
  - "Does this look like a good match for YOU?"
  - "What might be uncomfortable or undesirable for YOU based on your preferences?"
  - "How you can use this information to make a choice."

Remember:
You are the coordinator. You glue all the agents and tools together into one coherent experience for the user, without doing the scoring yourself.
""",
        tools=[
            detect_intent,
            load_long_term_profile,
            save_long_term_profile,
            save_onboarding_profile,  # For onboarding flow
            should_update_profile,
            detect_product_category,
            analyze_food_product,
            analyze_cosmetics_product,
            analyze_household_product,
        ],
    )
    
    return orchestrator

