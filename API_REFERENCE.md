# FOR ME API Reference

Complete API documentation for FOR ME Product Compatibility System.

## Base URL

```
Production: https://for-me-agent-xxxxx.run.app
Local: http://localhost:8080
```

## Authentication

Currently, authentication is handled via the `X-User-Id` header. Each user must provide a stable identifier.

**Header:**
```
X-User-Id: <user_id>
```

**Note:** In future versions, API keys or OAuth tokens may be required.

## Rate Limits

**Current limits:**
- 100 requests per minute per user
- 1000 requests per hour per user

**Rate limit headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1633024800
```

**Note:** Rate limiting is currently a stub and will be implemented in future versions.

## Error Codes

| Status Code | Description | Example |
|------------|-------------|---------|
| 400 | Bad Request - Invalid input parameters | Missing `user_id` or `ingredient_text` |
| 404 | Not Found - Resource doesn't exist | Invalid endpoint |
| 422 | Unprocessable Entity - Validation error | Invalid image format |
| 500 | Internal Server Error | System error during processing |

## Endpoints

### 1. Health Check

Check if the service is running.

**Endpoint:** `GET /health`

**Request:**
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "FOR ME Agent"
}
```

---

### 2. Root (API Information)

Get API information and available endpoints.

**Endpoint:** `GET /`

**Request:**
```bash
curl http://localhost:8080/
```

**Response:**
```json
{
  "service": "FOR ME Product Compatibility Agent",
  "version": "1.0.0",
  "endpoints": {
    "chat": "/chat (main endpoint - text input)",
    "chat_upload": "/chat/upload (image upload with OCR)",
    "analyze": "/analyze (legacy)",
    "onboarding": "/onboarding (legacy)",
    "health": "/health"
  }
}
```

---

### 3. Chat (Main Endpoint)

Main chat endpoint that handles all user interactions:
- New user onboarding (automatic if profile missing)
- Profile updates
- Reaction reporting
- Product analysis
- Small talk / help

**Endpoint:** `POST /chat`

**Headers:**
```
X-User-Id: <user_id> (required)
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "string (optional) - user's chat message",
  "ingredient_text": "string (optional) - raw ingredient list",
  "product_domain": "string (optional) - hint: cosmetics|food|household",
  "session_id": "string (optional) - for conversation continuity"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8080/chat \
  -H "X-User-Id: user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze this shampoo",
    "ingredient_text": "Water, SLS, Glycerin, Fragrance",
    "product_domain": "cosmetics"
  }'
```

**Success Response (200):**
```json
{
  "status": "success",
  "reply": "🎯 FOR ME Score: 65/100\n\n⚠️ Issues:\n• Fragrance: you noted sensitivity to fragrance\n• SLS: may be an irritant\n\n✅ Positive aspects:\n• Glycerin: hydrating ingredient that matches your hair goals\n\nThis is not medical advice or a diagnosis – it is a preference-based compatibility check based only on the information you shared.",
  "for_me_score": 65,
  "intent": "PRODUCT_ANALYSIS",
  "category": "cosmetics",
  "safety_issues": [],
  "sensitivity_issues": [
    "Fragrance: you noted sensitivity to fragrance",
    "SLS: may be an irritant"
  ]
}
```

**Error Response (400):**
```json
{
  "detail": "Either 'message' or 'ingredient_text' must be provided"
}
```

**Error Response (400):**
```json
{
  "detail": "X-User-Id header or user_id in body is required"
}
```

**Error Response (500):**
```json
{
  "detail": "Internal server error message"
}
```

---

### 4. Analyze Product (Legacy)

Legacy endpoint for product analysis. Prefer using `/chat` with `ingredient_text`.

**Endpoint:** `POST /analyze`

**Request Body:**
```json
{
  "user_id": "string (required)",
  "ingredient_text": "string (required)",
  "product_domain": "string (optional) - cosmetics|food|household",
  "session_id": "string (optional)"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "ingredient_text": "Sugar, cocoa butter, whole milk powder, hazelnut",
    "product_domain": "food"
  }'
```

**Success Response (200):**
```json
{
  "status": "success",
  "reply": "🎯 FOR ME Score: 15/100\n\n⚠️ Issues:\n• Hazelnut: contains component from strict_avoid list (hazelnut)\n• Sugar: you prefer to avoid components like 'sugar'\n\nThis is not medical advice or a diagnosis – it is a preference-based compatibility check based only on the information you shared.",
  "for_me_score": 15,
  "intent": "PRODUCT_ANALYSIS",
  "category": "food",
  "safety_issues": [
    "Hazelnut: contains component from strict_avoid list (hazelnut)"
  ],
  "sensitivity_issues": [
    "Sugar: you prefer to avoid components like 'sugar'"
  ],
  "has_strict_allergen_explicit": true
}
```

**Error Response (400):**
```json
{
  "detail": "ingredient_text is required"
}
```

---

### 5. Onboarding (Legacy)

Legacy endpoint for user onboarding. Prefer using `/chat` which automatically triggers onboarding if profile is missing.

**Endpoint:** `POST /onboarding`

**Request Body:**
```json
{
  "user_id": "string (required)",
  "user_responses": "string (optional) - user's responses to onboarding questions",
  "session_id": "string (optional)"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8080/onboarding \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "user_responses": "I'm allergic to nuts and prefer to avoid high salt"
  }'
```

**Success Response (200):**
```json
{
  "status": "success",
  "user_id": "user_123",
  "session_id": "onboarding_user_123",
  "response": "Thank you! 🙌 I saved your preferences and known reactions. From now on, FOR ME will use this profile to evaluate ingredients and show a personalized FOR ME Score for each product.",
  "profile": {
    "food_strict_avoid": [{"ingredient": "nuts", "type": "allergen"}],
    "food_prefer_avoid": [{"ingredient": "high_salt", "type": "preference"}],
    "cosmetics_sensitivities": [],
    "hair_type": null,
    "hair_goals": [],
    "skin_type": null,
    "skin_goals": []
  }
}
```

**Error Response (400):**
```json
{
  "detail": "user_id is required"
}
```

---

### 6. Chat with Image Upload (OCR)

Upload an image of product ingredients for OCR extraction and analysis.

**Endpoint:** `POST /chat/upload`

**Headers:**
```
X-User-Id: <user_id> (required)
Content-Type: multipart/form-data
```

**Form Data:**
- `image`: Image file (required) - JPEG, PNG, or WebP
- `message`: string (optional) - user message
- `product_domain`: string (optional) - cosmetics|food|household
- `session_id`: string (optional)

**Example Request:**
```bash
curl -X POST http://localhost:8080/chat/upload \
  -H "X-User-Id: user_123" \
  -F "image=@product_ingredients.jpg" \
  -F "message=Analyze this product" \
  -F "product_domain=cosmetics"
```

**Success Response (200):**
```json
{
  "status": "success",
  "reply": "🎯 FOR ME Score: 75/100\n\n✅ Positive aspects:\n• Glycerin: hydrating ingredient\n• Hyaluronic acid: matches your hydration goals\n\nThis is not medical advice or a diagnosis – it is a preference-based compatibility check based only on the information you shared.",
  "for_me_score": 75,
  "intent": "PRODUCT_ANALYSIS",
  "category": "cosmetics",
  "safety_issues": [],
  "sensitivity_issues": [],
  "extracted_text": "Water, Glycerin, Hyaluronic Acid, Fragrance, Phenoxyethanol",
  "ocr_status": "success"
}
```

**Error Response (400):**
```json
{
  "detail": "X-User-Id header is required"
}
```

**Error Response (400):**
```json
{
  "detail": "Invalid image format. Supported: JPEG, PNG, WebP"
}
```

**Error Response (400):**
```json
{
  "detail": "OCR failed: Unable to extract text from image"
}
```

---

## Response Schemas

### Chat Response Schema

```json
{
  "status": "success" | "error",
  "reply": "string - human-readable response (no score breakdown)",
  "for_me_score": number (0-100, optional) - final FOR ME score (only for product analysis),
  "intent": "ONBOARDING_REQUIRED" | "PROFILE_UPDATE" | "REACTIONS_AND_PREFERENCES" | "PRODUCT_ANALYSIS" | "SMALL_TALK",
  "category": "food" | "cosmetics" | "household" (optional),
  "safety_issues": ["string"] (optional) - list of safety issues,
  "sensitivity_issues": ["string"] (optional) - list of sensitivity issues,
  "has_strict_allergen_explicit": boolean (optional) - true if strict allergen found,
  "has_strict_allergen_traces": boolean (optional) - true if traces found,
  "extracted_text": "string (optional, for /chat/upload)",
  "ocr_status": "success" | "error" (optional, for /chat/upload)
}
```

### Error Response Schema

```json
{
  "detail": "string - error message"
}
```

---

## Usage Examples

### Python Example

```python
import requests

# Base URL
BASE_URL = "http://localhost:8080"

# Headers
headers = {
    "X-User-Id": "user_123",
    "Content-Type": "application/json"
}

# Analyze a product
response = requests.post(
    f"{BASE_URL}/chat",
    headers=headers,
    json={
        "message": "Analyze this product",
        "ingredient_text": "Water, SLS, Glycerin, Fragrance",
        "product_domain": "cosmetics"
    }
)

result = response.json()
print(f"FOR ME Score: {result.get('for_me_score')}")
print(f"Reply: {result.get('reply')}")
```

### JavaScript Example

```javascript
const BASE_URL = 'http://localhost:8080';

async function analyzeProduct(userId, ingredientText) {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'X-User-Id': userId,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: 'Analyze this product',
      ingredient_text: ingredientText,
      product_domain: 'cosmetics'
    })
  });
  
  const result = await response.json();
  console.log(`FOR ME Score: ${result.for_me_score}`);
  console.log(`Reply: ${result.reply}`);
}

// Usage
analyzeProduct('user_123', 'Water, SLS, Glycerin, Fragrance');
```

### cURL Example

```bash
# Health check
curl http://localhost:8080/health

# Analyze product
curl -X POST http://localhost:8080/chat \
  -H "X-User-Id: user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "ingredient_text": "Water, SLS, Glycerin, Fragrance",
    "product_domain": "cosmetics"
  }'

# Upload image
curl -X POST http://localhost:8080/chat/upload \
  -H "X-User-Id: user_123" \
  -F "image=@product.jpg" \
  -F "product_domain=cosmetics"
```

---

## Best Practices

1. **Always provide `X-User-Id` header** for user identification
2. **Use `/chat` endpoint** for all interactions (it handles onboarding automatically)
3. **Provide `session_id`** for conversation continuity
4. **Include `product_domain`** when known to improve category detection
5. **Handle errors gracefully** - check `status` field in responses
6. **Cache user profiles** to reduce API calls
7. **Use image upload** for better UX when users have product photos

---

## Support

For issues, questions, or feature requests, please contact the development team.

**API Version:** 2.0.0  
**Last Updated:** 2024

