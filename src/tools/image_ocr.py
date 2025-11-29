"""
Image OCR Tool

Extracts ingredient text from product images using Gemini Vision API.
"""

import base64
import io
from typing import Dict, Any, Optional
import os

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def extract_text_from_image(image_data: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
    """
    Extracts text from an image using Gemini Vision API.
    
    Args:
        image_data: Raw image bytes
        mime_type: MIME type of the image (image/jpeg, image/png, etc.)
    
    Returns:
        Dictionary with status and extracted text:
        - Success: {"status": "success", "text": "extracted text"}
        - Error: {"status": "error", "error_message": "..."}
    """
    if not GENAI_AVAILABLE:
        return {
            "status": "error",
            "error_message": "google-genai package not installed. Install with: pip install google-genai"
        }
    
    try:
        # Get API key from environment
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "error_message": "GOOGLE_API_KEY environment variable not set"
            }
        
        # Initialize Gemini client
        client = genai.Client(api_key=api_key)
        
        # Prepare prompt for OCR
        prompt = """Extract all ingredient text from this product image.

Focus on:
- Ingredient lists (INCI names, chemical names, food ingredients)
- Product composition text
- Any text related to ingredients or composition

Return ONLY the extracted ingredient text, without any additional commentary.
If no ingredients are found, return "No ingredients found".

Format: Extract text exactly as it appears, one ingredient per line if possible.
"""
        
        # Prepare content with image and prompt
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(
                        data=image_data,
                        mime_type=mime_type
                    ),
                    types.Part.from_text(text=prompt)
                ]
            )
        ]
        
        # Generate content with vision model
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for accurate extraction
                top_p=0.8,
            )
        )
        
        # Extract text from response
        extracted_text = ""
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        extracted_text += part.text
        
        if not extracted_text or extracted_text.strip().lower() == "no ingredients found":
            return {
                "status": "error",
                "error_message": "No ingredient text found in image"
            }
        
        return {
            "status": "success",
            "text": extracted_text.strip()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"OCR failed: {str(e)}"
        }


def validate_image_format(image_data: bytes, mime_type: str) -> Dict[str, Any]:
    """
    Validates image format and size.
    
    Args:
        image_data: Raw image bytes
        mime_type: MIME type of the image
    
    Returns:
        Dictionary with validation result
    """
    # Supported formats
    supported_formats = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    
    if mime_type.lower() not in supported_formats:
        return {
            "status": "error",
            "error_message": f"Unsupported image format: {mime_type}. Supported: {', '.join(supported_formats)}"
        }
    
    # Check file size (max 20MB for Gemini Vision)
    max_size = 20 * 1024 * 1024  # 20MB
    if len(image_data) > max_size:
        return {
            "status": "error",
            "error_message": f"Image too large: {len(image_data)} bytes. Maximum size: {max_size} bytes (20MB)"
        }
    
    if len(image_data) == 0:
        return {
            "status": "error",
            "error_message": "Empty image data"
        }
    
    return {
        "status": "success"
    }

