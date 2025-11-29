"""
FOR ME System

Main system orchestrator that sets up all agents and provides entry point.
"""

import logging
from typing import Dict, Any, Optional, Union

from google.adk.apps.app import App
from .types import (
    UserProfile,
    AgentResponse,
    AnalysisRequest,
    ScoreResult,
)
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from google.genai import types

from .agents import (
    create_router_agent,
    create_onboarding_agent,
    load_long_term_profile,
)
from .agents.orchestrator_agent import create_orchestrator_agent
from .memory import get_long_term_profile, is_profile_minimal, DEFAULT_EMPTY_PROFILE

# Session ID prefixes
ONBOARDING_SESSION_PREFIX = "onboarding_"
ANALYSIS_SESSION_PREFIX = "analysis_"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ForMeSystem:
    """
    Main FOR ME system orchestrator.
    
    Manages all agents, session service, and provides entry point for analysis.
    """
    
    def __init__(
        self,
        use_persistent_storage: bool = False,
        db_url: str = "sqlite:///for_me_data.db",
        model_name: str = "gemini-2.5-flash-lite",
    ):
        """
        Initialize FOR ME system.
        
        Args:
            use_persistent_storage: If True, use DatabaseSessionService; else InMemorySessionService
            db_url: Database URL for persistent storage
            model_name: Gemini model to use
        """
        self.model_name = model_name
        self.use_persistent_storage = use_persistent_storage
        
        # Configure retry options
        self.retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=7,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504],
        )
        
        # Initialize session service
        if use_persistent_storage:
            self.session_service = DatabaseSessionService(db_url=db_url)
            logger.info(f"Using persistent storage: {db_url}")
        else:
            self.session_service = InMemorySessionService()
            logger.info("Using in-memory storage")
        
        # Create onboarding agent
        logger.info("Creating onboarding agent...")
        self.onboarding_agent = create_onboarding_agent(
            retry_config=self.retry_config,
        )
        
        # Create onboarding app and runner
        self.onboarding_app = App(
            name="for_me_onboarding_app",
            root_agent=self.onboarding_agent,
        )
        self.onboarding_runner = Runner(
            app=self.onboarding_app,
            session_service=self.session_service,
        )
        
        # Create orchestrator agent (main chat handler)
        logger.info("Creating orchestrator agent...")
        self.orchestrator_agent = create_orchestrator_agent(
            retry_config=self.retry_config,
        )
        
        # Create router agent (for backward compatibility and direct product analysis)
        logger.info("Creating router agent...")
        self.router_agent = create_router_agent(
            retry_config=self.retry_config,
        )
        
        # Create App with orchestrator as root agent
        self.app = App(
            name="for_me_app",
            root_agent=self.orchestrator_agent,
        )
        
        # Create Runner
        self.runner = Runner(
            app=self.app,
            session_service=self.session_service,
        )
        
        logger.info("FOR ME system initialized successfully")
    
    def _is_profile_incomplete(self, profile: UserProfile) -> bool:
        """
        Checks if profile is incomplete.
        
        Profile is considered incomplete if:
        - food_strict_avoid + cosmetics_sensitivities + household_strict_avoid are all empty AND
        - food_prefer_avoid is empty AND
        - hair_goals + skin_goals + cosmetics_preferences are all empty
        
        Args:
            profile: User profile dictionary
        
        Returns:
            True if profile is incomplete, False otherwise
        """
        food_strict_avoid = profile.get("food_strict_avoid", [])
        cosmetics_sensitivities = profile.get("cosmetics_sensitivities", [])
        household_strict_avoid = profile.get("household_strict_avoid", [])
        food_prefer_avoid = profile.get("food_prefer_avoid", [])
        hair_goals = profile.get("hair_goals", [])
        skin_goals = profile.get("skin_goals", [])
        cosmetics_preferences = profile.get("cosmetics_preferences", [])
        
        # Profile is incomplete if all key fields are empty
        return (
            not food_strict_avoid and
            not cosmetics_sensitivities and
            not household_strict_avoid and
            not food_prefer_avoid and
            not hair_goals and
            not skin_goals and
            not cosmetics_preferences
        )
    
    async def _get_user_profile(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Loads user profile from session state.
        
        Checks both main session and onboarding session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
        
        Returns:
            User profile dictionary or None if not found
        """
        profile_key = f"user:{user_id}:long_profile"
        
        # Try to load from onboarding session
        try:
            onboarding_session = await self.session_service.get_session(
                app_name=self.onboarding_app.name,
                user_id=user_id,
                session_id=f"{ONBOARDING_SESSION_PREFIX}{user_id}",
            )
            if profile_key in onboarding_session.state:
                return onboarding_session.state[profile_key]
        except (ValueError, KeyError, AttributeError) as e:
            logger.debug(f"Could not load profile from onboarding session: {e}")
        
        # Try to load from main session
        try:
            session = await self.session_service.get_session(
                app_name=self.app.name,
                user_id=user_id,
                session_id=session_id,
            )
            if profile_key in session.state:
                return session.state[profile_key]
        except (ValueError, KeyError, AttributeError) as e:
            logger.debug(f"Could not load profile from main session: {e}")
        
        # Profile not found
        return None
    
    async def run_onboarding(
        self,
        user_id: str,
        user_responses: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Runs onboarding process for a new user.
        
        Args:
            user_id: User identifier
            user_responses: Optional user responses (for testing)
            session_id: Optional session ID
        
        Returns:
            Onboarding result with saved profile
        """
        if session_id is None:
            session_id = f"{ONBOARDING_SESSION_PREFIX}{user_id}"
        
        from google.genai import types as genai_types
        
        # Create or get session
        try:
            session = await self.session_service.create_session(
                app_name=self.onboarding_app.name,
                user_id=user_id,
                session_id=session_id,
            )
        except (ValueError, KeyError, AttributeError) as e:
            # Session might already exist, try to get it
            logger.debug(f"Session creation failed, trying to get existing: {e}")
            session = await self.session_service.get_session(
                app_name=self.onboarding_app.name,
                user_id=user_id,
                session_id=session_id,
            )
        
        # If user already provided responses (for testing)
        if user_responses:
            message = f"""Collect profile for user {user_id} based on the following responses:

{user_responses}

Use save_onboarding_profile tool to save the profile."""
        else:
            # Start onboarding with friendly greeting
            message = f"""Welcome to FOR ME! 👋

I'll help you find products that are perfect for you. 
To create your personal profile and calculate accurate FOR ME Score, 
I need to learn a bit about you.

Start collecting profile for user {user_id}, asking questions one by one:

1. About known reactions to ingredients or products (e.g., nuts, 
   lactose, certain colorings or fragrances)

2. About skin type (dry, oily, sensitive, combination)

3. About hair type (straight, wavy, curly, dry, oily)

4. About any reactions to products they've noticed (itching, redness, 
   irritation, bloating, etc.)

Be friendly, warm, ask questions naturally, one by one. 
Explain that this information will help find the perfect composition and calculate 
accurate FOR ME Score for each product.

After collecting answers, use save_onboarding_profile tool to save the profile."""
        
        user_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=message)]
        )
        
        logger.info(f"Starting onboarding for user {user_id}, session {session_id}")
        
        # Run onboarding
        response_parts = []
        async for event in self.onboarding_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_parts.append(part.text)
        
        response_text = "\n".join(response_parts) if response_parts else "Onboarding completed."
        
        # Check that profile is saved
        final_session = await self.session_service.get_session(
            app_name=self.onboarding_app.name,
            user_id=user_id,
            session_id=session_id,
        )
        profile_key = f"user:{user_id}:long_profile"
        saved_profile = final_session.state.get(profile_key)
        
        logger.info(f"Onboarding complete for user {user_id}. Profile saved: {saved_profile is not None}")
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "response": response_text,
            "profile": saved_profile,
        }
    
    async def analyze_product(
        self,
        user_id: str,
        ingredient_text: str,
        product_domain: Optional[str] = None,
        session_id: Optional[str] = None,
        skip_onboarding: bool = False,
    ) -> AgentResponse:
        """
        Analyze product compatibility for a user.
        
        First checks for profile existence. If profile is missing or incomplete,
        runs onboarding before analysis.
        
        This is the main entry point for external callers. It wires together
        agents, tools, memory and observability to provide compatibility analysis.
        
        Args:
            user_id: User identifier
            ingredient_text: Raw ingredient list text
            product_domain: Optional domain hint (cosmetics/food/household)
            session_id: Optional session ID (for conversation continuity)
            skip_onboarding: If True, skips onboarding check (for testing)
        
        Returns:
            Analysis result with FOR ME score and explanation
        """
        # Input validation
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id must be a non-empty string")
        if not ingredient_text or not isinstance(ingredient_text, str) or not ingredient_text.strip():
            raise ValueError("ingredient_text must be a non-empty string")
        if product_domain and product_domain not in ["food", "cosmetics", "household"]:
            logger.warning(f"Invalid product_domain: {product_domain}, will auto-detect")
            product_domain = None
        
        if session_id is None:
            session_id = f"{ANALYSIS_SESSION_PREFIX}{user_id}"
        
        # Step 1: Check for profile existence
        if not skip_onboarding:
            profile = await self._get_user_profile(user_id, f"onboarding_{user_id}")
            
            if profile is None or self._is_profile_incomplete(profile):
                logger.info(f"Profile not found or incomplete for user {user_id}. Starting onboarding...")
                # Run onboarding
                onboarding_result = await self.run_onboarding(
                    user_id=user_id,
                    session_id=f"{ONBOARDING_SESSION_PREFIX}{user_id}",
                )
                # Reload profile after onboarding
                profile = await self._get_user_profile(user_id, f"onboarding_{user_id}")
                
                # Early return if profile still not saved after onboarding
                if profile is None or self._is_profile_incomplete(profile):
                    return {
                        "status": "error",
                        "reply": "Profile not saved after onboarding. Please try again.",
                        "user_id": user_id,
                        "session_id": session_id,
                    }
                
                logger.info(f"Onboarding completed for user {user_id}. Proceeding with analysis...")
            else:
                logger.info(f"Profile found for user {user_id}. Skipping onboarding.")
        
        # Step 2: Run main analysis with multi-agent architecture
        # Ensure ingredient_text is ASCII-safe
        ingredient_text = ingredient_text or ""
        ingredient_text = ingredient_text.encode("ascii", "ignore").decode()
        
        # Create user message for RouterAgent
        if product_domain:
            message = f"""Analyze this {product_domain} product for user {user_id}:

Ingredients:
{ingredient_text}

CRITICAL: Use the multi-agent architecture with category separation!

Use tools in the following order:
1. detect_product_category - determine product category (food/cosmetics/household)
   Parameters: ingredient_text="{ingredient_text}", product_domain="{product_domain}"
2. load_user_profile - load user profile (user_id: {user_id})
3. Based on category, call the corresponding agent:
   - If category == "food": analyze_food_product(user_id="{user_id}", ingredient_text="...")
   - If category == "cosmetics": analyze_cosmetics_product(user_id="{user_id}", ingredient_text="...")
   - If category == "household": analyze_household_product(user_id="{user_id}", ingredient_text="...")

Then provide final response with:
- FOR ME Score (0-100)
- Detailed compatibility explanation based on category
- Key issues (only from profile)
- Positive aspects
- Disclaimer (without word "medical")"""
        else:
            message = f"""Analyze this product for user {user_id}:

Ingredients:
{ingredient_text}

CRITICAL: Use the multi-agent architecture with category separation!

Use tools in the following order:
1. detect_product_category - determine product category (food/cosmetics/household)
   Parameters: ingredient_text="{ingredient_text}"
2. load_user_profile - load user profile (user_id: {user_id})
3. Based on category, call the corresponding agent:
   - If category == "food": analyze_food_product(user_id="{user_id}", ingredient_text="...")
   - If category == "cosmetics": analyze_cosmetics_product(user_id="{user_id}", ingredient_text="...")
   - If category == "household": analyze_household_product(user_id="{user_id}", ingredient_text="...")

Then provide final response with:
- FOR ME Score (0-100)
- Detailed compatibility explanation based on category
- Key issues (only from profile)
- Positive aspects
- Disclaimer (without word "medical")"""
        
        from google.genai import types as genai_types
        user_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=message)]
        )
        
        logger.info(f"Starting analysis for user {user_id}, session {session_id}")
        
        # Create session first if it doesn't exist
        try:
            session = await self.session_service.create_session(
                app_name=self.app.name,
                user_id=user_id,
                session_id=session_id,
            )
        except (ValueError, KeyError, AttributeError) as e:
            # Session might already exist, try to get it
            logger.debug(f"Session creation failed, trying to get existing: {e}")
            session = await self.session_service.get_session(
                app_name=self.app.name,
                user_id=user_id,
                session_id=session_id,
            )
        
        # Ensure long-term profile is available in session state for tools
        # Load profile from onboarding session or create default
        session.state.setdefault("short_term_context", {})
        profile_key = f"user:{user_id}:long_profile"
        
        # If profile not yet loaded in this session, load from onboarding session
        if profile_key not in session.state:
            import copy
            if profile and isinstance(profile, dict):
                # Copy profile from onboarding session to current session
                session.state[profile_key] = copy.deepcopy(profile)
                logger.info(f"Profile copied from onboarding session to analysis session for user {user_id}")
            else:
                # Default profile
                session.state[profile_key] = copy.deepcopy(DEFAULT_EMPTY_PROFILE)

        # Save short-term context (latest recipe) in session state
        session.state["short_term_context"] = {
            "ingredient_text": ingredient_text,
            "product_domain": product_domain,
        }

        # Run analysis
        response_parts = []
        last_event = None
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            last_event = event
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_parts.append(part.text)
        
        # Extract final response (ADK guarantees last model event is final)
        if not response_parts:
            try:
                final_session = await self.session_service.get_session(
                    app_name=self.app.name,
                    user_id=user_id,
                    session_id=session_id,
                )
                # Get last model output (ADK guarantees last model event is final)
                for event in reversed(final_session.events):
                    if event.content:
                        event_text = None
                        if hasattr(event.content, 'parts'):
                            text_parts = []
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(part.text)
                            if text_parts:
                                event_text = "\n".join(text_parts)
                        elif hasattr(event.content, 'text') and event.content.text:
                            event_text = event.content.text
                        
                        if event_text and event_text.strip():
                            response_parts = [event_text]
                            break
                    
            except Exception as e:
                logger.debug(f"Could not get response from session: {e}")
        
        response_text = "\n".join(response_parts) if response_parts else "Analysis completed. System processed the request, but final response was not extracted. Please check logs or retry the request."
        
        logger.info(f"Analysis complete for user {user_id}")
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "response": response_text,
            "ingredient_text": ingredient_text,
        }
    
    async def setup_user_profile(
        self,
        user_id: str,
        health_notes: list | None = None,  # Deprecated: kept for backward compatibility
        avoid_categories: list | None = None,  # Deprecated: use food_strict_avoid, cosmetics_sensitivities, household_strict_avoid
        avoid_ingredients: list | None = None,  # Deprecated: use food_prefer_avoid
        goals: list | None = None,  # Deprecated: use hair_goals, skin_goals, cosmetics_preferences
        learned_patterns: list | None = None,  # Deprecated: use repeated_negative_reactions
        strict_avoid: list | None = None,
        prefer_avoid: list | None = None,
        # Category-specific fields (recommended)
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
    ):
        """
        Setup or update user profile directly (programmatic API).
        
        Used for programmatic profile setup without onboarding.
        
        Note: Legacy fields (health_notes, avoid_categories, avoid_ingredients, goals, learned_patterns)
        are deprecated but kept for backward compatibility. Use category-specific fields instead.
        """
        session_id = f"profile_{user_id}"
        
        # Create or get session
        try:
            session = await self.session_service.create_session(
                app_name=self.app.name,
                user_id=user_id,
                session_id=session_id,
            )
        except Exception:
            session = await self.session_service.get_session(
                app_name=self.app.name,
                user_id=user_id,
                session_id=session_id,
            )
        
        # Create mock ToolContext for direct call to save_long_term_profile
        from .agents.profile_agent import save_long_term_profile
        
        class SimpleContext:
            def __init__(self, state):
                self.state = state
        
        tool_context = SimpleContext(session.state)
        
        save_long_term_profile(
            tool_context=tool_context,
            user_id=user_id,
            health_notes=health_notes,
            avoid_categories=avoid_categories,
            avoid_ingredients=avoid_ingredients,
            goals=goals,
            learned_patterns=learned_patterns,
            strict_avoid=strict_avoid,
            prefer_avoid=prefer_avoid,
            food_strict_avoid=food_strict_avoid,
            food_prefer_avoid=food_prefer_avoid,
            food_ok_if_small=food_ok_if_small,
            cosmetics_sensitivities=cosmetics_sensitivities,
            cosmetics_preferences=cosmetics_preferences,
            household_strict_avoid=household_strict_avoid,
            household_sensitivities=household_sensitivities,
            hair_type=hair_type,
            hair_goals=hair_goals,
            skin_type=skin_type,
            skin_goals=skin_goals,
        )
        
        logger.info(f"Long-term profile saved for user {user_id}")
    
    async def handle_chat_request(
        self,
        user_id: str,
        message: Optional[str] = None,
        ingredient_text: Optional[str] = None,
        product_domain: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AgentResponse:
        """
        Handle chat request from user.
        
        Args:
            user_id: User identifier (required)
            message: User's chat message (optional)
            ingredient_text: Raw ingredient list (optional)
            product_domain: Domain hint: cosmetics/food/household (optional)
            session_id: Session identifier (optional)
        
        Returns:
            Dictionary with:
            - reply: Human-readable response (no score breakdown shown)
            - for_me_score: Final FOR ME score (0-100, only for product analysis)
            - intent: Detected intent
            - category: Product category (if analysis)
            - safety_issues: List of safety issues (if analysis)
            - sensitivity_issues: List of sensitivity issues (if analysis)
            - has_strict_allergen_explicit: Boolean flag (if analysis)
            - has_strict_allergen_traces: Boolean flag (if analysis)
            - status: success/error
            
            Note: Internal scores (safety_score, sensitivity_score, match_score) are NOT exposed.
        """
        # Input validation
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id must be a non-empty string")
        if not message and not ingredient_text:
            raise ValueError("Either message or ingredient_text must be provided")
        if product_domain and product_domain not in ["food", "cosmetics", "household"]:
            logger.warning(f"Invalid product_domain: {product_domain}, will auto-detect")
            product_domain = None
        """
        Main chat entry point for FOR ME system.
        
        This is the single public entrypoint that handles all chat interactions:
        - New user onboarding (if profile is missing/minimal)
        - Profile updates
        - Reaction reporting
        - Product analysis
        - Small talk / help
        
        Args:
            user_id: Stable user identifier (from X-User-Id header)
            message: User's chat message
            ingredient_text: Optional raw ingredient list
            product_domain: Optional hint (cosmetics|food|household)
            session_id: Optional session identifier for conversation continuity
        
        Returns:
            Chat response with:
            - reply: Human-readable response (no score breakdown shown)
            - for_me_score: Final FOR ME score (0-100, only for product analysis)
            - intent: Detected intent
            - category: Product category (if analysis)
            - safety_issues: List of safety issues (if analysis)
            - sensitivity_issues: List of sensitivity issues (if analysis)
            - has_strict_allergen_explicit: Boolean flag (if analysis)
            - has_strict_allergen_traces: Boolean flag (if analysis)
            - status: success/error
            
            Note: Internal scores (safety_score, sensitivity_score, match_score) are NOT exposed.
        """
        if session_id is None:
            session_id = f"chat_{user_id}"
        
        from google.genai import types as genai_types
        
        # Create or get session
        try:
            session = await self.session_service.create_session(
                app_name=self.app.name,
                user_id=user_id,
                session_id=session_id,
            )
        except Exception:
            session = await self.session_service.get_session(
                app_name=self.app.name,
                user_id=user_id,
                session_id=session_id,
            )
        
        # Ensure profile is available in session state for tools
        profile_key = f"user:{user_id}:long_profile"
        profile_loaded = False
        
        if profile_key not in session.state:
            # Try to load from onboarding session
            try:
                onboarding_session = await self.session_service.get_session(
                    app_name=self.onboarding_app.name,
                    user_id=user_id,
                    session_id=f"{ONBOARDING_SESSION_PREFIX}{user_id}",
                )
                if profile_key in onboarding_session.state:
                    import copy
                    session.state[profile_key] = copy.deepcopy(
                        onboarding_session.state[profile_key]
                    )
                    profile_loaded = True
            except Exception:
                pass
        
        # Check if profile is minimal - if so, run onboarding FIRST
        if not profile_loaded or profile_key not in session.state:
            from .memory import get_long_term_profile, is_profile_minimal
            class SimpleContext:
                def __init__(self, state):
                    self.state = state
            
            temp_context = SimpleContext(session.state)
            profile = get_long_term_profile(temp_context, user_id)
            
            if is_profile_minimal(profile):
                logger.info(f"Profile is minimal for user {user_id}. Running onboarding first...")
                # Run onboarding before processing chat request
                onboarding_result = await self.run_onboarding(
                    user_id=user_id,
                    session_id=f"{ONBOARDING_SESSION_PREFIX}{user_id}",
                )
                # Reload profile after onboarding
                try:
                    onboarding_session = await self.session_service.get_session(
                        app_name=self.onboarding_app.name,
                        user_id=user_id,
                        session_id=f"{ONBOARDING_SESSION_PREFIX}{user_id}",
                    )
                    if profile_key in onboarding_session.state:
                        import copy
                        session.state[profile_key] = copy.deepcopy(
                            onboarding_session.state[profile_key]
                        )
                        logger.info(f"Profile loaded after onboarding for user {user_id}")
                except Exception as e:
                    logger.warning(f"Could not load profile after onboarding: {e}")
        
        # Ensure ingredient_text is ASCII-safe
        if ingredient_text:
            ingredient_text = ingredient_text.encode("ascii", "ignore").decode()
        
        # Build message for orchestrator
        chat_message_parts = []
        if message:
            chat_message_parts.append(message)
        if ingredient_text:
            chat_message_parts.append(f"\nIngredient list:\n{ingredient_text}")
        if product_domain:
            chat_message_parts.append(f"\nProduct domain hint: {product_domain}")
        
        chat_message = "\n".join(chat_message_parts) if chat_message_parts else (
            message or ingredient_text or "Hello"
        )
        
        user_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=chat_message)]
        )
        
        logger.info(
            f"Chat request for user {user_id}, "
            f"message_length={len(message or '')}, "
            f"has_ingredients={bool(ingredient_text)}"
        )
        
        # Run orchestrator
        response_parts = []
        
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            if event.content:
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_parts.append(part.text)
                elif hasattr(event.content, 'text') and event.content.text:
                    response_parts.append(event.content.text)
        
        # Extract final response (ADK guarantees last model event is final)
        if not response_parts:
            try:
                final_session = await self.session_service.get_session(
                    app_name=self.app.name,
                    user_id=user_id,
                    session_id=session_id,
                )
                # Get last model output (ADK guarantees last model event is final)
                for event in reversed(final_session.events):
                    if event.content:
                        event_text = None
                        if hasattr(event.content, 'parts'):
                            text_parts = []
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(part.text)
                            if text_parts:
                                event_text = "\n".join(text_parts)
                        elif hasattr(event.content, 'text') and event.content.text:
                            event_text = event.content.text
                        
                        if event_text and event_text.strip():
                            response_parts = [event_text]
                            break
            except Exception as e:
                logger.debug(f"Could not get response from session: {e}")
        
        response_text = "\n".join(response_parts) if response_parts else "I received your message. Let me process that for you."
        
        # Try to extract final score and issues if this was a product analysis
        # Category agents store results in session state
        final_score = None
        safety_issues = []
        sensitivity_issues = []
        category = None
        has_strict_allergen_explicit = None
        has_strict_allergen_traces = None
        
        try:
            # Look for analysis results in session state
            # Check various possible keys where results might be stored
            possible_keys = [
                f"analysis_result_{user_id}",
                "last_analysis_result",
                "product_analysis_result",
            ]
            
            for key in possible_keys:
                if key in session.state:
                    result = session.state[key]
                    if isinstance(result, dict):
                        final_score = result.get("for_me_score")
                        if final_score is not None:
                            # Keep safety and sensitivity issues separate
                            safety_issues = result.get("safety_issues", [])
                            sensitivity_issues = result.get("sensitivity_issues", [])
                            category = result.get("category")
                            has_strict_allergen_explicit = result.get("has_strict_allergen_explicit")
                            has_strict_allergen_traces = result.get("has_strict_allergen_traces")
                            break
            
            # Also check session events for tool results
            if final_score is None:
                for event in reversed(session.events):
                    if hasattr(event, 'tool_result') and event.tool_result:
                        result_data = event.tool_result
                        if isinstance(result_data, dict):
                            if "for_me_score" in result_data:
                                final_score = result_data.get("for_me_score")
                                # Keep safety and sensitivity issues separate
                                safety_issues = result_data.get("safety_issues", [])
                                sensitivity_issues = result_data.get("sensitivity_issues", [])
                                category = result_data.get("category")
                                has_strict_allergen_explicit = result_data.get("has_strict_allergen_explicit")
                                has_strict_allergen_traces = result_data.get("has_strict_allergen_traces")
                                break
        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.warning(f"Could not extract score: {e}")
        
        # Detect intent (simplified - orchestrator should have done this)
        intent = "SMALL_TALK"
        if ingredient_text:
            intent = "PRODUCT_ANALYSIS"
        elif final_score is not None:
            intent = "PRODUCT_ANALYSIS"
        else:
            # Check if onboarding was triggered
            profile = get_long_term_profile(
                type('ToolContext', (), {'state': session.state})(),
                user_id
            )
            if is_profile_minimal(profile):
                intent = "ONBOARDING_REQUIRED"
        
        logger.info(f"Chat response for user {user_id}, intent={intent}")
        
        # Build response with only final score (no sub-scores)
        # Internal scores (safety_score, sensitivity_score, match_score) are NOT exposed
        response = {
            "reply": response_text,
            "intent": intent,
            "status": "success",
        }
        
        # Only add score-related fields if this was a product analysis
        if final_score is not None:
            response["for_me_score"] = final_score
            if safety_issues:
                response["safety_issues"] = safety_issues
            if sensitivity_issues:
                response["sensitivity_issues"] = sensitivity_issues
            if category:
                response["category"] = category
            if has_strict_allergen_explicit is not None:
                response["has_strict_allergen_explicit"] = has_strict_allergen_explicit
            if has_strict_allergen_traces is not None:
                response["has_strict_allergen_traces"] = has_strict_allergen_traces
        
        return response

