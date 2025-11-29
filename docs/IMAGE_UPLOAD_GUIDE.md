# 📸 Image Upload & OCR Guide

## Overview

FOR ME supports uploading product ingredient photos with automatic text recognition via Gemini Vision API.

## Endpoint: `/chat/upload`

### Description

Uploads a product image, extracts ingredient text via OCR, and analyzes it as a regular `/chat` request.

### Request Format

**Method:** `POST`  
**Content-Type:** `multipart/form-data`  
**Headers:**
- `X-User-Id` (required): User identifier

**Form Fields:**
- `image` (required): Image file (JPEG, PNG, WebP)
- `message` (optional): User message text
- `product_domain` (optional): Domain hint (`cosmetics`, `food`, `household`)
- `session_id` (optional): Session identifier

### Response Format

```json
{
    "reply": "Your FOR ME Score is 85%...",
    "for_me_score": 85,
    "safety_issues": [],
    "sensitivity_issues": ["Fragrance: you noted sensitivity to fragrance"],
    "extracted_text": "AQUA, GLYCERIN, DIMETHICONE, PARFUM...",
    "ocr_status": "success",
    "intent": "PRODUCT_ANALYSIS",
    "category": "cosmetics",
    "status": "success"
}
```

## Usage Examples

### cURL

```bash
curl -X POST "http://localhost:8000/chat/upload" \
  -H "X-User-Id: user_001" \
  -F "image=@/path/to/product_photo.jpg" \
  -F "message=Analyze this product" \
  -F "product_domain=cosmetics"
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/chat/upload"
headers = {"X-User-Id": "user_001"}

with open("product_photo.jpg", "rb") as image_file:
    files = {"image": image_file}
    data = {
        "message": "Analyze this product",
        "product_domain": "cosmetics"
    }
    response = requests.post(url, headers=headers, files=files, data=data)
    print(response.json())
```

### JavaScript (fetch)

```javascript
const formData = new FormData();
formData.append('image', imageFile);
formData.append('message', 'Analyze this product');
formData.append('product_domain', 'cosmetics');

fetch('http://localhost:8000/chat/upload', {
  method: 'POST',
  headers: {
    'X-User-Id': 'user_001'
  },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## Supported Formats

- **JPEG/JPG** (`image/jpeg`)
- **PNG** (`image/png`)
- **WebP** (`image/webp`)

**Limitations:**
- Maximum file size: 20MB
- Good image quality recommended for better OCR accuracy

## How It Works

1. **Image Upload** → Format and size validation
2. **OCR Processing** → Gemini Vision API extracts text
3. **Ingredient Parsing** → Standard parser processes extracted text
4. **Analysis** → System analyzes as regular `/chat` request
5. **Response** → Returns result + extracted text

## Error Handling

### Validation Errors (400)

```json
{
    "detail": "Unsupported image format: image/gif. Supported: image/jpeg, image/png, image/webp"
}
```

```json
{
    "detail": "Image too large: 25000000 bytes. Maximum size: 20971520 bytes (20MB)"
}
```

### OCR Errors (400)

```json
{
    "detail": "OCR failed: No ingredient text found in image"
}
```

### Server Errors (500)

```json
{
    "detail": "Internal server error message"
}
```

## Best Practices

1. **Image Quality:**
   - Good lighting
   - Sharp focus
   - Direct angle
   - High contrast text on background

2. **Shooting Area:**
   - Focus on ingredient list
   - Avoid blur
   - Ensure all text is visible

3. **Processing:**
   - System automatically crops/normalizes text
   - OCR extracts only ingredient text
   - Extracted text available in response for verification

## Integration with Existing Flow

After OCR processing, extracted text is passed to standard `handle_chat_request`, so:
- ✅ Onboarding supported (if profile missing)
- ✅ Product categorization works
- ✅ All scoring rules apply
- ✅ Explanation generated

## Debugging

If OCR doesn't work:
1. Check `GOOGLE_API_KEY` is set
2. Check image format and size
3. Look at `extracted_text` in response - what was extracted
4. Ensure image contains ingredient text

## Example Images

**Good Examples:**
- ✅ Clear ingredient list on packaging
- ✅ Label with INCI names
- ✅ Product composition from app

**Bad Examples:**
- ❌ Blurry image
- ❌ Poor lighting
- ❌ Angled shot
- ❌ Image without text
