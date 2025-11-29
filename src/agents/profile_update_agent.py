"""
Profile Update Agent (A2A)

Receives user statements about reactions/sensitivities.
Decides whether to update long-term memory.
Outputs updates to profile.
"""

from typing import Dict, Any, Optional
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.tools.tool_context import ToolContext

from .profile_agent import load_user_profile
from ..memory import (
    update_long_term_profile,
    add_repeated_negative_reaction,
    get_long_term_profile,
)


def should_update_profile(
    tool_context: ToolContext,
    user_id: str,
    user_statement: str,
) -> Dict[str, Any]:
    """
    Analyzes user statement and decides if profile should be updated.
    
    Looks for:
    - Repeated negative reactions ("this shampoo causes itching every time")
    - New sensitivities ("I noticed I'm sensitive to fragrance")
    - Positive experiences ("glycerin works well for my dry skin")
    
    Returns:
        Dictionary with update recommendations
    """
    profile = get_long_term_profile(tool_context, user_id)
    
    # Simple keyword-based detection (can be enhanced with LLM)
    statement_lower = user_statement.lower()
    
    updates = {}
    
    # Check for repeated negative reactions
    reaction_keywords = [
        "causes", "caused", "always", "every time", "consistently",
        "reaction", "itching", "irritation", "redness", "breakout",
        "bloating", "stomach", "headache", "rash",
    ]
    
    if any(kw in statement_lower for kw in reaction_keywords):
        # Try to extract ingredient and reaction
        # This is simplified - in production, use LLM for extraction
        updates["repeated_negative_reactions"] = [{
            "statement": user_statement,
            "needs_review": True,
        }]
    
    # Check for sensitivities
    sensitivity_keywords = ["sensitive to", "allergic to", "avoid", "can't use"]
    if any(kw in statement_lower for kw in sensitivity_keywords):
        # Extract ingredient if possible
        updates["potential_sensitivity"] = user_statement
    
    return {
        "status": "success",
        "should_update": len(updates) > 0,
        "updates": updates,
        "recommendation": "Review and update profile if statement contains health observations",
    }


def create_profile_update_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Creates Profile Update Agent that processes user statements about reactions.

    Args:
        retry_config: HTTP retry configuration

    Returns:
        Configured ProfileUpdateAgent
    """
    agent = LlmAgent(
        name="profile_update_agent",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        description="Analyzes user statements about reactions/sensitivities and proposes updates to the long-term profile.",
        instruction="""You are the Profile Update Agent for FOR ME.

Your role:
1. Analyze user statements about reactions, sensitivities, or experiences.
2. Decide whether this information is STABLE enough to go into long-term memory.
3. Propose structured updates to the profile (you do NOT have to apply them yourself if the caller only wants a plan).

CRITICAL RULES:
- Only suggest updates for stable patterns (repeated reactions, long-term preferences).
- Do NOT store full product histories or raw ingredient lists.
- Treat all health-related information as user-reported experience, NOT medical data.
- Prefer adding:
  - repeated_negative_reactions
  - cosmetics_sensitivities / household_sensitivities / food_* fields
  - preferences like prefer_avoid

Examples:
- "this shampoo causes scalp itching every time" → add to repeated_negative_reactions (domain: cosmetics).
- "I'm sensitive to fragrance" → add 'fragrance' to cosmetics_sensitivities.
- "I always get bloating from milk chocolate" → repeated_negative_reactions (domain: food).

Output format:
{
  "should_update": true/false,
  "updates": {
    "repeated_negative_reactions": [...],
    "cosmetics_sensitivities": [...],
    "food_prefer_avoid": [...],
    ...
  },
  "recommendation": "short natural language summary"
}

You have tools:
- load_user_profile: to inspect the current profile.
- should_update_profile: a simple helper tool that can suggest minimal updates based on raw text.

If you need to, you may call tools to assist, then build a cleaner, more structured JSON response.
""",
        tools=[
            load_user_profile,
            should_update_profile,
        ],
    )

    return agent

