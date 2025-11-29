"""
Entrypoint for FOR ME System

This module provides the main system initialization for deploying FOR ME
on Cloud Run (FastAPI) or other platforms.
"""

import os
import logging
from typing import Dict, Any, Optional

from src.system import ForMeSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize global system instance
# Use persistent storage for production deployment
_system: Optional[ForMeSystem] = None


def get_system() -> ForMeSystem:
    """
    Get or create the global ForMeSystem instance.
    
    Uses lazy initialization to avoid issues during import.
    
    For Cloud Run deployment, uses in-memory storage by default.
    Set USE_PERSISTENT_STORAGE=true and DATABASE_URL for production database.
    
    Returns:
        ForMeSystem instance
    """
    global _system
    if _system is None:
        # For Cloud Run, use in-memory by default (can be overridden with env vars)
        # For production with database, set USE_PERSISTENT_STORAGE=true and DATABASE_URL
        use_persistent = os.getenv("USE_PERSISTENT_STORAGE", "false").lower() == "true"
        db_url = os.getenv("DATABASE_URL", "sqlite:///for_me_data.db")
        
        _system = ForMeSystem(
            use_persistent_storage=use_persistent,
            db_url=db_url,
        )
        logger.info(f"ForMeSystem initialized (persistent={use_persistent})")
    
    return _system


async def handle_chat_request(
    user_id: str,
    message: Optional[str] = None,
    ingredient_text: Optional[str] = None,
    product_domain: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main chat handler for FOR ME system.
    
    This is the single public entrypoint that handles all chat interactions.
    
    Args:
        user_id: User identifier
        message: User's chat message
        ingredient_text: Optional raw ingredient list text
        product_domain: Optional domain hint ("food", "cosmetics", "household")
        session_id: Optional session identifier for conversation continuity
    
    Returns:
        A JSON-serializable dict with chat response
    """
    try:
        system = get_system()
        logger.info(
            f"Chat request for user {user_id}, "
            f"message_length={len(message or '')}, "
            f"has_ingredients={bool(ingredient_text)}"
        )
        
        result = await system.handle_chat_request(
            user_id=user_id,
            message=message,
            ingredient_text=ingredient_text,
            product_domain=product_domain,
            session_id=session_id,
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        return {
            "status": "error",
            "error_message": str(e),
            "reply": f"An error occurred: {e}",
            "intent": "error",
        }

