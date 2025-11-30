# Project Overview - FOR ME

**FOR ME** is a production-grade multi-agent system that transforms ingredient lists (cosmetics, food, household products) into personalized compatibility scores for individual users. The system analyzes products and provides a **FOR ME Score (0–100%)** — a compatibility assessment based on user allergies, sensitivities, goals, and domain-specific rules.

**Important:** The system is NOT medical — it provides compatibility assessments based on data that users themselves provide.

![Architecture](./docs/ARCHITECTURE_DIAGRAM.md "FOR ME System Architecture")

## Problem Statement

Understanding product compatibility is challenging because ingredient lists are long, multi-language, and confusing. Most solutions provide generic advice that doesn't account for individual differences. Every person has unique allergies, sensitivities, dietary rules, and product preferences. Manually checking every ingredient against personal constraints is time-consuming, error-prone, and mentally exhausting. Users need a personalized system that can instantly analyze any product composition and answer one simple question: **"Is this good for *me*?"**

## Solution Statement

FOR ME uses a multi-agent system to automatically parse ingredient lists, detect product categories, analyze risks against user profiles, and generate personalized compatibility scores. Agents can handle multi-language ingredient lists, route products to category-specific analysis engines (food, cosmetics, household), apply domain-specific scoring rules, and provide clear, non-medical explanations. The system learns from user feedback and adjusts future scores based on repeated negative reactions, transforming product analysis from a manual, error-prone process into an instant, personalized compatibility assessment.

## Architecture

Core to FOR ME is the **OrchestratorAgent** — a prime example of a multi-agent system. It's not a monolithic application but an ecosystem of specialized agents, each contributing to a different stage of the product analysis process. This modular approach, facilitated by Google's Agent Development Kit, allows for sophisticated and robust workflows.

![Architecture](./docs/ARCHITECTURE_DIAGRAM.md "FOR ME Multi-Agent Architecture")

The **OrchestratorAgent** is constructed using the `LlmAgent` class from the Google ADK. Its definition highlights several key parameters: the `name`, the `model` it uses for reasoning capabilities (Gemini 2.5 Flash Lite), and detailed `instruction` sets that govern its behavior. Crucially, it also defines the `tools` it has at its disposal and the routing logic for delegating tasks to specialized agents.

The real power of FOR ME lies in its team of specialized agents, each an expert in its domain.

**Orchestrator: `orchestrator_agent`**

This agent is the main coordinator responsible for detecting user intent, routing requests to appropriate agents, aggregating results, and formatting user-friendly responses. It always calls `detect_intent` as a tool to determine whether the user wants product analysis, profile updates, onboarding, or general chat. For product analysis, it routes through category detection to the appropriate compatibility agent.

**Onboarding Specialist: `onboarding_agent`**

This agent collects user profiles through structured dialogue. It asks about allergies, sensitivities, dietary rules, and product preferences in a friendly, non-medical way. Once enough information is gathered, it calls `save_onboarding_profile` to store the structured profile data.

**Profile Manager: `profile_agent`**

The profile agent manages user profiles using long-term and short-term memory. It loads existing profiles, saves updates, and ensures data consistency. It handles the rich, multi-level profile schema including food-specific fields (`food_strict_avoid`, `food_prefer_avoid`), cosmetics-specific fields (`cosmetics_sensitivities`, `hair_type`, `skin_goals`), and household-specific fields.

**Category-Specific Analysts: `food_compatibility_agent`, `cosmetics_compatibility_agent`, `household_compatibility_agent`**

These agents are experts in their respective domains. Each implements domain-specific scoring logic:
- **Food Agent**: Strict safety rules (50% weight on safety, 30% sensitivity, 20% match)
- **Cosmetics Agent**: Soft recommendations (30% safety, 30% sensitivity, 40% match)
- **Household Agent**: Balanced approach (40% safety, 30% sensitivity, 30% match)

Each agent calculates Safety, Sensitivity, and Match scores based on ingredient risks, user profile constraints, and positive ingredient matches.

**Profile Update Specialist: `profile_update_agent`**

This agent analyzes user statements about reactions and sensitivities. It decides whether information is stable enough to go into long-term memory and proposes structured updates to the profile, such as adding to `repeated_negative_reactions` or updating category-specific sensitivity lists.

## Essential Tools and Utilities

The FOR ME system and its agents are equipped with a variety of tools to perform their tasks effectively.

**Ingredient Parser (`parse_ingredients`)**

This tool parses raw ingredient text (which may be multi-language, poorly formatted, or contain OCR errors) into a normalized list of ingredient names. It handles common separators, removes extra whitespace, and normalizes ingredient names for consistent matching.

**Risk Dictionary (`get_ingredient_risks`)**

This tool maps normalized ingredient names to risk tags (e.g., "fragrance", "high_salt", "drying_alcohol", "harsh_surfactant"). It provides structured risk information that agents use to calculate sensitivity scores and generate safety issues.

**Category Detection (`detect_product_category`)**

This tool determines whether a product belongs to the food, cosmetics, or household category. It first checks for explicit domain hints, then parses ingredients and counts keyword matches across category-specific dictionaries. This ensures products are routed to the correct compatibility agent.

**Product Analysis Tools (`analyze_food_product`, `analyze_cosmetics_product`, `analyze_household_product`)**

These tools implement the agent-as-a-tool (A2A) pattern. Each tool:
1. Loads the user profile from long-term memory
2. Parses and normalizes the ingredient list
3. Gets risk mappings from the risk dictionary
4. Builds structured context for the compatibility agent
5. Calculates scores using category-specific logic
6. Returns structured results with scores and issues

**Memory System (`memory.py`)**

The memory system separates long-term (user profile) and short-term (session context) memory. It uses `deepcopy` to prevent shared mutable state, validates profile completeness, and applies repeated negative reactions to scores. The system ensures that profile updates are type-safe and that minimal profiles trigger onboarding flows.

**Observability (`observability.py`)**

The observability system provides enterprise-grade logging, metrics, and request tracing. It tracks tool calls, latencies, token usage, and request flows. All logs are ASCII-safe and include defensive copying to prevent shared mutation issues.

## Conclusion

The beauty of FOR ME lies in its modular, category-aware workflow. The OrchestratorAgent acts as a project manager, coordinating the efforts of its specialized team. It delegates tasks based on product category, gathers user feedback, and ensures that each stage of the analysis process is completed successfully. This multi-agent coordination, powered by the Google ADK, results in a system that is modular, reusable, and scalable.

FOR ME is a compelling demonstration of how multi-agent systems, built with powerful frameworks like Google's Agent Development Kit, can tackle complex, real-world problems. By breaking down the process of product compatibility analysis into a series of manageable tasks and assigning them to specialized agents, it creates a workflow that is both efficient and robust.

## Value Statement

FOR ME transforms raw ingredient lists into personalized compatibility insights in seconds, eliminating the need for manual ingredient checking. The system handles multi-language ingredient lists, applies domain-specific scoring rules, and learns from user feedback to improve accuracy over time. Users can instantly compare products, understand risks, and make informed decisions based on their personal profile.

If I had more time, I would add an agent to scan product databases and automatically update ingredient risk dictionaries based on new research. This would require integrating with external APIs or building custom web scraping tools.

## Installation

This project was built against Python 3.11+.

It is suggested you create a virtual environment using your preferred tooling (e.g., `venv`, `uv`).

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set API Key

**Option 1: Using .env file (Recommended)**

```bash
# Copy the template
cp .env.example .env

# Edit .env and add your API key
# GOOGLE_API_KEY=your-api-key-here
```

**Option 2: Environment variable**

```bash
export GOOGLE_API_KEY='your-api-key-here'
```

Get API key: https://aistudio.google.com/app/api-keys

> ⚠️ **Important**: Never commit `.env` file to git! It's already in `.gitignore`.

### 4. Run the Server

```bash
python main.py
```

The server will start on `http://localhost:8080`

### Running Tests

**Run the evaluation suite:**

```bash
python -m src.eval
```

**Run API tests:**

```bash
# Start server first
python main.py

# In another terminal
python test_api.py
```

**Run bot tests:**

```bash
python test_bot.py
```

## Project Structure

The project is organized as follows:

*   `src/`: The main Python package for the system.
    *   `system.py`: Defines the main `ForMeSystem` class and orchestrates all agents.
    *   `memory.py`: Implements long-term and short-term memory management.
    *   `observability.py`: Provides logging, metrics, and request tracing.
    *   `eval.py`: Contains the evaluation framework for quality testing.
    *   `types.py`: Defines common type aliases and TypedDict structures.
    *   `agents/`: Contains the individual agents, each responsible for a specific task.
        *   `orchestrator_agent.py`: Main coordinator that routes requests.
        *   `onboarding_agent.py`: Collects user profile through structured dialogue.
        *   `profile_agent.py`: Manages user profiles and memory.
        *   `profile_update_agent.py`: Analyzes user statements and proposes profile updates.
        *   `food_compatibility_agent.py`: Calculates compatibility scores for food products.
        *   `cosmetics_compatibility_agent.py`: Calculates compatibility scores for cosmetics.
        *   `household_compatibility_agent.py`: Calculates compatibility scores for household products.
        *   `scoring_agent.py`: General scoring logic (legacy, category agents now handle scoring).
        *   `explainer_agent.py`: Generates user-friendly explanations.
        *   `category_tools.py`: Tools for category detection and product analysis.
    *   `tools/`: Defines the custom tools used by the agents.
        *   `ingredient_parser.py`: Parses raw ingredient text into normalized lists.
        *   `risk_dictionary.py`: Maps ingredients to risk tags.
        *   `category_dictionaries.py`: Category-specific keyword dictionaries.
        *   `image_ocr.py`: OCR tool for extracting text from product images.
*   `main.py`: FastAPI server entrypoint.
*   `vertex_agent_entrypoint.py`: System initialization entrypoint for Cloud Run.
*   `deploy_to_cloud_run.py`: Deployment script for Google Cloud Run.
*   `tests/`: Contains unit tests and integration tests.
*   `docs/`: Contains documentation files.
    *   `ARCHITECTURE.md`: Detailed system architecture documentation.
    *   `ARCHITECTURE_DIAGRAM.md`: Mermaid diagrams for system architecture.
    *   `IMAGE_UPLOAD_GUIDE.md`: Guide for using image OCR feature.
*   `API_REFERENCE.md`: Complete API documentation for all endpoints.

## Workflow

The FOR ME system follows this workflow:

1.  **User Input**: User sends a message with ingredient text (or uploads an image for OCR).

2.  **Intent Detection**: The OrchestratorAgent calls `detect_intent` to determine user intent:
    - `ONBOARDING_REQUIRED`: User needs to complete profile setup
    - `PRODUCT_ANALYSIS`: User wants to analyze a product
    - `PROFILE_UPDATE`: User wants to update their profile
    - `REACTIONS_AND_PREFERENCES`: User describes reactions or preferences
    - `SMALL_TALK`: General questions about the system

3.  **Onboarding (if needed)**: If the profile is incomplete, the OnboardingAgent collects:
    - Allergies and strict avoidances
    - Sensitivities and preferences
    - Goals (hydration, avoiding salt, etc.)
    - Optional health notes (non-medical)

4.  **Category Detection**: For product analysis, the system calls `detect_product_category`:
    - Checks explicit domain hint
    - Parses ingredients
    - Counts keyword matches
    - Determines category (food, cosmetics, household)

5.  **Product Analysis**: Routes to the appropriate analysis tool:
    - `analyze_food_product` → FoodCompatibilityAgent
    - `analyze_cosmetics_product` → CosmeticsCompatibilityAgent
    - `analyze_household_product` → HouseholdCompatibilityAgent

6.  **Score Calculation**: Each category agent:
    - Loads user profile from memory
    - Parses ingredients using `parse_ingredients`
    - Gets risks using `get_ingredient_risks`
    - Calculates Safety, Sensitivity, and Match scores
    - Applies repeated negative reactions penalties
    - Computes final FOR ME Score using category-specific weights

7.  **Response Formatting**: The OrchestratorAgent formats the response:
    - Single FOR ME Score (0-100)
    - Combined issues list (safety + sensitivity)
    - Category and intent
    - User-friendly explanation

8.  **Profile Updates**: If the user describes reactions, the ProfileUpdateAgent:
    - Analyzes the statement
    - Proposes structured updates
    - Updates `repeated_negative_reactions` or category-specific fields

## API Endpoints

Once the server is running, you can use these endpoints:

- `GET /health` - Health check
- `GET /` - API information
- `POST /chat` - Main chat endpoint (requires `X-User-Id` header)
- `POST /analyze` - Legacy analysis endpoint
- `POST /onboarding` - Start onboarding flow
- `POST /chat/upload` - Upload image for OCR analysis

**Example:**

```bash
curl -X POST http://localhost:8080/chat \
  -H "X-User-Id: test_user_001" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze this shampoo",
    "ingredient_text": "Water, SLS, Glycerin, Fragrance",
    "product_domain": "cosmetics"
  }'
```

**📖 For complete API documentation, see [API_REFERENCE.md](./API_REFERENCE.md)**

## Documentation

- **[API Reference](./API_REFERENCE.md)** - Complete API documentation for all endpoints
- **[Architecture](./docs/ARCHITECTURE.md)** - Detailed system architecture and design
- **[Architecture Diagrams](./docs/ARCHITECTURE_DIAGRAM.md)** - Mermaid diagrams for visualization
- **[Image Upload Guide](./docs/IMAGE_UPLOAD_GUIDE.md)** - How to use image OCR feature
- **[Unit Tests](./tests/README.md)** - Test suite documentation

## Deployment

### Cloud Run

```bash
python deploy_to_cloud_run.py
```

### Docker

```bash
docker build -t for-me-agent .
docker run -p 8080:8080 -e GOOGLE_API_KEY=your-key for-me-agent
```

## Course Concepts Used

This project demonstrates:

- ✅ **Multi-Agent System** — 10 specialized agents working together
- ✅ **Agent-as-a-Tool (A2A)** — Orchestration pattern for agent composition
- ✅ **Tools** — Custom function tools (parser, risk dictionary, OCR)
- ✅ **Sessions & Memory** — Explicit long-term/short-term memory separation
- ✅ **Context Engineering** — Structured context building for agents
- ✅ **Observability** — Logging, metrics, and request tracing
- ✅ **Evaluation** — Behavioral quality gate for regression testing
- ✅ **Model & Tools Layer** — Gemini API + structured tools integration

## License

This project was created for educational purposes as part of the "5-Day AI Agents Intensive" course.

## Acknowledgments

Built with:
- Google Agent Development Kit (ADK)
- Gemini API
- FastAPI
- Google Cloud Run
