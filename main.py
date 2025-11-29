"""
Main FastAPI server for FOR ME Agent on Cloud Run

Single /chat endpoint for all interactions.
Supports image uploads for OCR ingredient extraction.
"""

from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form
from typing import Optional
from vertex_agent_entrypoint import get_system
from src.tools.image_ocr import extract_text_from_image, validate_image_format
import uvicorn
import os

app = FastAPI(title="FOR ME Agent API", version="2.0.0")


@app.post("/chat")
async def chat(
    request: dict,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """
    Main chat endpoint for FOR ME system.
    
    This is the single public entrypoint that handles:
    - New user onboarding (automatic if profile missing)
    - Profile updates
    - Reaction reporting
    - Product analysis
    - Small talk / help
    
    Headers:
        X-User-Id: Stable user identifier (required)
    
    Request body:
    {
        "message": "string (optional) - user's chat message",
        "ingredient_text": "string (optional) - raw ingredient list",
        "product_domain": "string (optional) - hint: cosmetics|food|household"
    }
    
    Response:
    {
        "reply": "string - human-readable response (no score breakdown)",
        "for_me_score": number (optional) - final FOR ME score (0-100) if product analysis,
        "intent": "string - detected intent",
        "category": "string (optional) - food|cosmetics|household",
        "safety_issues": ["string"] (optional) - list of safety issues,
        "sensitivity_issues": ["string"] (optional) - list of sensitivity issues,
        "has_strict_allergen_explicit": boolean (optional) - true if strict allergen found,
        "has_strict_allergen_traces": boolean (optional) - true if traces found,
        "status": "success|error"
    }
    """
    try:
        # Get user_id from header or request body
        user_id = x_user_id or request.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="X-User-Id header or user_id in body is required"
            )

        message = request.get("message")
        ingredient_text = request.get("ingredient_text")
        product_domain = request.get("product_domain")
        session_id = request.get("session_id")

        # At least one of message or ingredient_text must be provided
        if not message and not ingredient_text:
            raise HTTPException(
                status_code=400,
                detail="Either 'message' or 'ingredient_text' must be provided"
            )

        system = get_system()
        result = await system.handle_chat_request(
            user_id=user_id,
            message=message,
            ingredient_text=ingredient_text,
            product_domain=product_domain,
            session_id=session_id,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_product(request: dict):
    """
    Analyze product compatibility.
    
    Request body:
    {
        "user_id": "string",
        "ingredient_text": "string",
        "product_domain": "string (optional)",
        "session_id": "string (optional)"
    }
    """
    try:
        user_id = request.get("user_id", "default_user")
        ingredient_text = request.get("ingredient_text", "")
        product_domain = request.get("product_domain")
        session_id = request.get("session_id")

        if not ingredient_text:
            raise HTTPException(
                status_code=400, detail="ingredient_text is required"
            )

        system = get_system()
        result = await system.handle_chat_request(
            user_id=user_id,
            message=None,
            ingredient_text=ingredient_text,
            product_domain=product_domain,
            session_id=session_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "FOR ME Agent"}


@app.post("/onboarding")
async def onboarding(request: dict):
    """
    Run onboarding process to set up user profile.
    
    Request body:
    {
        "user_id": "string (required)",
        "user_responses": "string (optional) - user's responses to onboarding questions",
        "session_id": "string (optional)"
    }
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=400, detail="user_id is required"
            )

        user_responses = request.get("user_responses")
        session_id = request.get("session_id")

        system = get_system()
        result = await system.run_onboarding(
            user_id=user_id,
            user_responses=user_responses,
            session_id=session_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/upload")
async def chat_with_image(
    image: UploadFile = File(...),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    message: Optional[str] = Form(None),
    product_domain: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
):
    """
    Chat endpoint with image upload for OCR ingredient extraction.
    
    This endpoint allows users to upload a photo of product ingredients,
    which will be processed using OCR (Gemini Vision API) to extract text,
    and then analyzed like a normal /chat request.
    
    Headers:
        X-User-Id: Stable user identifier (required)
    
    Form data:
        image: Image file (required) - JPEG, PNG, or WebP
        message: Optional user message
        product_domain: Optional domain hint (cosmetics|food|household)
        session_id: Optional session identifier
    
    Response:
    {
        "reply": "string - human-readable response",
        "for_me_score": number (optional),
        "scores": {...} (optional),
        "extracted_text": "string - OCR extracted text",
        "intent": "string",
        "status": "success|error"
    }
    """
    try:
        # Get user_id from header
        user_id = x_user_id
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="X-User-Id header is required"
            )
        
        # Validate image format
        mime_type = image.content_type or "image/jpeg"
        image_data = await image.read()
        
        validation = validate_image_format(image_data, mime_type)
        if validation["status"] != "success":
            raise HTTPException(
                status_code=400,
                detail=validation.get("error_message", "Invalid image format")
            )
        
        # Extract text from image using OCR
        ocr_result = extract_text_from_image(image_data, mime_type)
        if ocr_result["status"] != "success":
            raise HTTPException(
                status_code=400,
                detail=f"OCR failed: {ocr_result.get('error_message', 'Unknown error')}"
            )
        
        extracted_text = ocr_result["text"]
        
        # Build user message if not provided
        user_message = message or f"Analyze ingredients from this image"
        
        # Process through normal chat flow with extracted text
        system = get_system()
        result = await system.handle_chat_request(
            user_id=user_id,
            message=user_message,
            ingredient_text=extracted_text,
            product_domain=product_domain,
            session_id=session_id,
        )
        
        # Add extracted text to response for transparency
        result["extracted_text"] = extracted_text
        result["ocr_status"] = "success"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "service": "FOR ME Product Compatibility Agent",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat (main endpoint - text input)",
            "chat_upload": "/chat/upload (image upload with OCR)",
            "analyze": "/analyze (legacy)",
            "onboarding": "/onboarding (legacy)",
            "health": "/health",
        },
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

