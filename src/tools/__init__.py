"""Custom tools for FOR ME agents."""

from .ingredient_parser import parse_ingredients
from .risk_dictionary import get_ingredient_risks

# Optional: Image OCR (requires google-genai)
try:
    from .image_ocr import extract_text_from_image, validate_image_format
    __all__ = ["parse_ingredients", "get_ingredient_risks", "extract_text_from_image", "validate_image_format"]
except ImportError:
    __all__ = ["parse_ingredients", "get_ingredient_risks"]

