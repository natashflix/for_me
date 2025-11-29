# FOR ME - System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FOR ME System                             │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          OrchestratorAgent (Main Entry Point)         │   │
│  │  - Detects user intent                                │   │
│  │  - Routes to appropriate agents/tools                 │   │
│  │  - Aggregates results                                 │   │
│  │  - Formats user-friendly responses                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│         ┌───────────────┼───────────────┐                    │
│         │               │               │                    │
│         ▼               ▼               ▼                    │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │Onboarding│   │  Profile │   │ Profile  │               │
│  │  Agent   │   │  Agent   │   │  Update  │               │
│  │          │   │          │   │  Agent   │               │
│  └──────────┘   └──────────┘   └──────────┘               │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Category Detection & Analysis Tools          │   │
│  │  - detect_product_category                           │   │
│  │  - analyze_food_product                              │   │
│  │  - analyze_cosmetics_product                          │   │
│  │  - analyze_household_product                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│         ┌───────────────┼───────────────┐                    │
│         │               │               │                    │
│         ▼               ▼               ▼                    │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │   Food   │   │Cosmetics │   │Household │               │
│  │Compatibility│Compatibility│Compatibility│              │
│  │   Agent  │   │  Agent   │   │  Agent   │               │
│  └──────────┘   └──────────┘   └──────────┘               │
│       │               │               │                      │
│       └───────────────┼───────────────┘                      │
│                       ▼                                      │
│              ┌──────────────┐                               │
│              │  Scoring      │                               │
│              │  (Internal)   │                               │
│              │  - Safety     │                               │
│              │  - Sensitivity │                               │
│              │  - Match      │                               │
│              │  - FOR ME Score│                              │
│              └──────────────┘                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

### 1. User Input

```
User Input:
  - user_id: "user_001"
  - message: "Analyze this shampoo" (optional)
  - ingredient_text: "Water, SLS, Glycerin, Fragrance"
  - product_domain: "cosmetics" (optional)
```

### 2. OrchestratorAgent

The OrchestratorAgent is the main coordinator that:
- **Always calls `detect_intent` tool first** to determine user intent
- Routes based on detected intent:
  - `ONBOARDING_REQUIRED` → OnboardingAgent
  - `PROFILE_UPDATE` → ProfileUpdateAgent
  - `REACTIONS_AND_PREFERENCES` → ProfileUpdateAgent
  - `PRODUCT_ANALYSIS` → Category detection → Category analysis tools
  - `SMALL_TALK` → Direct response

### 3. Intent Detection Tool

The `detect_intent` tool analyzes the request and returns:
- `ONBOARDING_REQUIRED` - New user, profile missing/minimal
- `PROFILE_UPDATE` - User updating preferences
- `REACTIONS_AND_PREFERENCES` - User reporting reactions
- `PRODUCT_ANALYSIS` - User wants to analyze a product
- `SMALL_TALK` - General questions/help

### 4. Category Detection Tool

For `PRODUCT_ANALYSIS` intent:
- `detect_product_category` tool determines domain:
  - Uses explicit `product_domain` hint if provided
  - Analyzes ingredient keywords
  - Returns: `"food"`, `"cosmetics"`, or `"household"`

### 5. Category Analysis Tools

Each category has a dedicated analysis tool that internally orchestrates:

#### 5a. Profile Loading
- Loads user profile from long-term memory via `load_user_profile` tool
- Profile structure:
  ```json
  {
    "food_strict_avoid": ["yellow-5", "nuts"],
    "food_prefer_avoid": ["high_salt"],
    "cosmetics_sensitivities": ["fragrance", "sls"],
    "cosmetics_preferences": ["silicone_free"],
    "hair_type": "curly",
    "hair_goals": ["hydration", "anti_frizz"],
    "skin_type": "sensitive",
    "skin_goals": ["hydration", "reduce_irritation"],
    "household_strict_avoid": ["bleach", "ammonia"],
    "repeated_negative_reactions": [
      {"ingredient": "sls", "domain": "cosmetics", "frequency": "always"}
    ]
  }
  ```

#### 5b. Ingredient Parsing
- Uses `parse_ingredients` tool (function tool, not agent)
- Input: `"Water, SLS, Glycerin, Fragrance"`
- Output: `["water", "sls", "glycerin", "fragrance"]`
- Normalizes ingredient names for consistent matching

#### 5c. Risk Identification
- Uses `get_ingredient_risks` tool (function tool, not agent)
- Input: `["water", "sls", "glycerin", "fragrance"]`
- Output:
  ```json
  {
    "risks": {
      "sls": ["harsh_surfactant", "sls"],
      "fragrance": ["fragrance", "irritant"],
      "glycerin": ["hydrating", "beneficial"]
    },
    "all_risk_tags": ["harsh_surfactant", "sls", "fragrance", "irritant", "hydrating", "beneficial"]
  }
  ```

#### 5d. Context Engineering
- Builds structured context via `build_X_context()` functions:
  - Combines profile, ingredients, risks
  - Applies category-specific dictionaries (FOOD_POSITIVE, COSMETICS_NEGATIVE, etc.)
  - Prepares context for scoring logic

#### 5e. Score Calculation
- Calls `calculate_X_scores()` functions (not separate agents):
  - `calculate_food_scores()` - Strict safety logic
  - `calculate_cosmetics_scores()` - Soft recommendations
  - `calculate_household_scores()` - Medium strictness
- Each function returns:
  ```json
  {
    "safety_score": 100,
    "sensitivity_score": 75,
    "match_score": 80,
    "for_me_score": 85,
    "final_cap": 100,
    "safety_issues": [...],
    "sensitivity_issues": [...],
    "risk_analysis": {...}
  }
  ```

### 6. Final Response Format

The OrchestratorAgent formats the response:
- **Only exposes `for_me_score`** (0-100) to the user
- **Hides internal scores** (safety_score, sensitivity_score, match_score)
- Combines `safety_issues` and `sensitivity_issues` in explanation
- Includes non-medical disclaimer

Example response:
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

## 🛠️ Tools

### Function Tools (Not Agents)

#### parse_ingredients
- **Type:** Function Tool
- **Input:** Raw ingredient text (string)
- **Output:** Normalized ingredient list (list of strings)
- **Example:**
  ```python
  parse_ingredients(tool_context, "Water, SLS, Glycerin")
  # → {"status": "success", "ingredients": ["water", "sls", "glycerin"]}
  ```

#### get_ingredient_risks
- **Type:** Function Tool
- **Input:** List of normalized ingredients
- **Output:** Risk mapping (ingredient → risk tags)
- **Example:**
  ```python
  get_ingredient_risks(tool_context, ["sls", "fragrance"])
  # → {
  #   "status": "success",
  #   "risks": {
  #     "sls": ["harsh_surfactant", "sls"],
  #     "fragrance": ["fragrance", "irritant"]
  #   }
  # }
  ```

#### detect_product_category
- **Type:** Function Tool
- **Input:** Ingredient text, optional product_domain hint
- **Output:** Detected category ("food" | "cosmetics" | "household")
- **Example:**
  ```python
  detect_product_category(tool_context, "Water, SLS, Glycerin", product_domain="cosmetics")
  # → {"status": "success", "category": "cosmetics", "confidence": "high"}
  ```

#### analyze_food_product / analyze_cosmetics_product / analyze_household_product
- **Type:** Function Tools (Agent-as-a-Tool pattern)
- **Input:** user_id, ingredient_text
- **Output:** Complete analysis with scores and issues
- **Internally orchestrates:** Profile loading → Parsing → Risk identification → Scoring

### Agent Tools (A2A Pattern)

#### OnboardingAgent
- **Purpose:** Collects user profile through structured dialogue
- **Tools:** `save_onboarding_profile`
- **Output:** Structured profile saved to long-term memory

#### ProfileAgent
- **Purpose:** Manages user profiles
- **Tools:** `load_user_profile`, `save_user_profile`
- **Output:** Profile data in structured format

#### ProfileUpdateAgent
- **Purpose:** Analyzes user statements about reactions/sensitivities
- **Tools:** `load_user_profile`, `should_update_profile`
- **Output:** Proposed profile updates (structured recommendations)

## 💾 Memory System

### Long-Term Memory

Stored in Session State (MVP) or Vertex AI Memory Bank (production):

```json
{
  "user:user_001:long_profile": {
    "food_strict_avoid": ["yellow-5", "nuts"],
    "food_prefer_avoid": ["high_salt"],
    "cosmetics_sensitivities": ["fragrance", "sls"],
    "cosmetics_preferences": ["silicone_free"],
    "hair_type": "curly",
    "hair_goals": ["hydration", "anti_frizz"],
    "skin_type": "sensitive",
    "skin_goals": ["hydration", "reduce_irritation"],
    "household_strict_avoid": ["bleach"],
    "repeated_negative_reactions": [
      {
        "ingredient": "sls",
        "domain": "cosmetics",
        "frequency": "always",
        "severity": "moderate"
      }
    ]
  }
}
```

### Short-Term Context

Tracks recent interactions and temporary state:

```json
{
  "user:user_001:short_context": {
    "recent_products": [...],
    "current_session_intent": "PRODUCT_ANALYSIS",
    "updated_at": "2024-01-15T10:30:00"
  }
}
```

## 📊 Scoring System

### Safety Score (0-100)
- **Strict allergens (explicit)** → Safety=0, final_cap=15
  - User marked ingredient as strict_avoid and it's present
  - Example: user avoids "nuts" → product contains "hazelnut paste" → Safety=0
- **Traces** → Safety≈20, final_cap≈40
  - Ingredient marked as strict_avoid appears in "may contain traces" form
- **No allergens** → Safety starts from 100

### Sensitivity Score (0-100)
- **Irritants** → -15 to -25 per match
  - Fragrance, drying alcohol, harsh surfactants
  - Only applies if user marked category in profile
- **For cosmetics:** Irritants affect Sensitivity, NOT Safety (unless strict_avoid)

### Match Score (0-100)
- Starts from 50 (neutral baseline)
- **Beneficial ingredients** → +15..20
  - Example: Glycerin + user goal "hydrate_skin" → +20 Match
- **Conflicting ingredients** → -15..20
  - Example: Drying alcohol + user goal "hydrate_skin" → -20 Match

### Final FOR ME Score

Category-specific weights:

- **Food:** `0.5 * Safety + 0.3 * Sensitivity + 0.2 * Match`
- **Cosmetics:** `0.3 * Safety + 0.3 * Sensitivity + 0.4 * Match`
- **Household:** `0.4 * Safety + 0.3 * Sensitivity + 0.3 * Match`

**Special Rules:**
- For severe allergens (Safety=0): score capped to 15–20 max
- `final_cap` mechanism ensures strict allergens cannot result in high scores
- Category-specific adjustments:
  - **Food:** Strictest rules, Safety=0 → final_cap=15
  - **Cosmetics:** Soft recommendations, Safety only drops with strict_avoid
  - **Household:** Medium strictness, depends on user profile

## 🔗 A2A Communication

Agents communicate through **AgentTool** (A2A Protocol):

```python
# Orchestrator Agent uses other agents as tools
orchestrator_agent = LlmAgent(
    tools=[
        AgentTool(agent=onboarding_agent),
        AgentTool(agent=profile_agent),
        # Function tools
        detect_intent,
        detect_product_category,
        analyze_food_product,
        analyze_cosmetics_product,
        analyze_household_product,
    ]
)
```

## 📊 Observability

### Logging
- All agent calls logged
- Key events (start, complete, error)
- Structured logs with request IDs

### Metrics
- Request count
- Response time
- Error rate
- Score distribution
- Agent call counts

### Tracing
- Full traceability through ADK web UI
- Visibility of all agent calls and tool invocations
- Request-level correlation

## ✅ Evaluation

### Unit Tests
- 56 unit tests covering:
  - Memory operations
  - Scoring calculations
  - Tool functions
  - Context builders
  - System helpers

### Test Coverage
- Core functionality covered
- Edge cases tested
- Type validation verified

## 🎯 Course Concepts Implementation

| Concept | Implementation |
|---------|---------------|
| **Multi-Agent System** | 7 specialized agents (Orchestrator, Onboarding, Profile, ProfileUpdate, Food, Cosmetics, Household) |
| **Tools** | parse_ingredients, get_ingredient_risks, detect_product_category, analyze_*_product |
| **Sessions & Memory** | InMemorySessionService / DatabaseSessionService |
| **Context Engineering** | Explicit context building via build_X_context() functions |
| **Observability** | Logging, metrics, tracing |
| **A2A Protocol** | AgentTool for inter-agent communication |
| **Evaluation** | Unit test suite with 56 tests |

## 🔄 Production Extensions

1. **Vertex AI Memory Bank** instead of Session State
2. **Extended Risk Dictionary** (more ingredients)
3. **More complex scoring logic** (ML-based)
4. **Cloud Logging & Monitoring** for observability
5. **Rate limiting** and caching
6. **Multi-language support**
7. **Image OCR** (already implemented via `/chat/upload`)
