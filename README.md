# FOR ME - Personalized Product Compatibility Agent

**FOR ME** is a production-grade multi-agent system that transforms ingredient lists (cosmetics, food, household products) into personalized compatibility scores for individual users.

## 🎯 Description

FOR ME analyzes products and provides a **FOR ME Score (0–100%)** — a compatibility assessment based on:
- User allergies and sensitivities
- User goals (hydration, avoiding salt, etc.)
- Risks in product composition
- Domain-specific rules (cosmetics vs food vs household products)

**Important:** The system is NOT medical — it provides compatibility assessments based on data that users themselves provide.

## 🚀 Quick Start

### 1. Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set API Key

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

### 3. Run the Server

```bash
python main.py
```

The server will start on `http://localhost:8080`

### 4. Test the API

```bash
# Health check
curl http://localhost:8080/health

# Chat endpoint
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

## 📚 Documentation

- **[API Reference](./API_REFERENCE.md)** - Complete API documentation for all endpoints
- **[Architecture](./docs/ARCHITECTURE.md)** - System architecture and design
- **[Unit Tests](./tests/README.md)** - Test suite documentation

## 📝 Main Entry Points

### Primary API

The main API is `ForMeSystem.handle_chat_request()`:

```python
import asyncio
from src.system import ForMeSystem

async def main():
    system = ForMeSystem(use_persistent_storage=False)
    
    result = await system.handle_chat_request(
        user_id="user_001",
        message="Analyze this shampoo",
        ingredient_text="Water, SLS, Glycerin, Fragrance",
        product_domain="cosmetics",
    )
    
    print(result["reply"])
    print(f"FOR ME Score: {result.get('for_me_score')}")

asyncio.run(main())
```

### API Endpoints

Once the server is running, you can use these endpoints:

- `GET /health` - Health check
- `GET /` - API information
- `POST /chat` - Main chat endpoint (requires `X-User-Id` header)
- `POST /analyze` - Legacy analysis endpoint
- `POST /onboarding` - Start onboarding flow
- `POST /chat/upload` - Upload image for OCR analysis

**Example:**

```python
import requests

response = requests.post(
    "http://localhost:8080/chat",
    headers={"X-User-Id": "user_001"},
    json={
        "message": "Analyze this product",
        "ingredient_text": "Water, SLS, Glycerin, Fragrance",
        "product_domain": "cosmetics"
    }
)
print(response.json())
```

## 🏗️ Architecture

See detailed documentation:
- [Full Architecture](./docs/ARCHITECTURE.md)
- [Image Upload Guide](./docs/IMAGE_UPLOAD_GUIDE.md)

### Multi-Agent Pipeline

```
[User Input] → [OrchestratorAgent] → [Category Detection] 
    → [FoodCompatibilityAgent | CosmeticsCompatibilityAgent | HouseholdCompatibilityAgent]
    → [ScoringAgent] → [ExplainerAgent] → [FOR ME Score + Explanation]
```

### Key Components

- **OrchestratorAgent**: Main coordinator, routes requests to appropriate agents
- **OnboardingAgent**: Collects user profile through structured dialogue
- **Category Agents**: Specialized agents for food, cosmetics, household products
- **ScoringAgent**: Calculates compatibility scores
- **ExplainerAgent**: Generates user-friendly explanations
- **Memory System**: Separates long-term (profile) and short-term (session) memory

## 📁 Project Structure

```
.
├── README.md                   # This file
├── requirements.txt            # Dependencies
├── main.py                     # FastAPI server entrypoint
├── Dockerfile                  # Docker image for Cloud Run
├── deploy_to_cloud_run.py      # Deployment script
├── vertex_agent_entrypoint.py  # System initialization entrypoint
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── src/                        # Main code package
│   ├── system.py               # Main system orchestrator
│   ├── memory.py               # Long-term/short-term memory
│   ├── eval.py                 # Quality evaluation suite
│   ├── observability.py        # Logging and metrics
│   ├── agents/                 # Agent implementations
│   │   ├── orchestrator_agent.py
│   │   ├── router_agent.py
│   │   ├── onboarding_agent.py
│   │   ├── profile_agent.py
│   │   ├── food_compatibility_agent.py
│   │   ├── cosmetics_compatibility_agent.py
│   │   ├── household_compatibility_agent.py
│   │   ├── explainer_agent.py
│   │   ├── profile_update_agent.py
│   │   ├── scoring_agent.py
│   │   └── category_tools.py
│   └── tools/                  # Custom tools
│       ├── ingredient_parser.py
│       ├── risk_dictionary.py
│       ├── category_dictionaries.py
│       └── image_ocr.py
└── docs/                       # Documentation
    ├── ARCHITECTURE.md
    ├── UPDATED_PITCH.md
    └── IMAGE_UPLOAD_GUIDE.md
```

## ⚠️ Limitations

- Category detection may misclassify rare products
- System is not medical advice; relies fully on user-provided profile data

## 🧪 Testing

### Run Evaluation Suite

```bash
python -m src.eval
```

### Run API Tests

```bash
# Start server first
python main.py

# In another terminal
python test_api.py
```

### Run Bot Tests

```bash
python test_bot.py
```

## 🚀 Deployment

### Cloud Run

```bash
python deploy_to_cloud_run.py
```

### Docker

```bash
docker build -t for-me-agent .
docker run -p 8080:8080 -e GOOGLE_API_KEY=your-key for-me-agent
```

## 📚 Documentation

- [Architecture](./docs/ARCHITECTURE.md) - Detailed system architecture
- [Architectural Pitch](./docs/UPDATED_PITCH.md) - Technical pitch and design decisions
- [Image Upload Guide](./docs/IMAGE_UPLOAD_GUIDE.md) - How to use image OCR feature

## 🎓 Course Concepts Used

This project demonstrates:

- ✅ **Multi-Agent System** — 10 specialized agents working together
- ✅ **Agent-as-a-Tool (A2A)** — Orchestration pattern for agent composition
- ✅ **Tools** — Custom function tools (parser, risk dictionary, OCR)
- ✅ **Sessions & Memory** — Explicit long-term/short-term memory separation
- ✅ **Context Engineering** — Structured context building for agents
- ✅ **Observability** — Logging, metrics, and request tracing
- ✅ **Evaluation** — Behavioral quality gate for regression testing
- ✅ **Model & Tools Layer** — Gemini API + structured tools integration

## 🔧 Development

### Code Quality

- Type hints throughout
- Comprehensive error handling
- Production-ready observability

### Adding New Features

1. **New Agent**: Create in `src/agents/` following existing patterns
2. **New Tool**: Add to `src/tools/` and register in appropriate agent
3. **New Category**: Extend category dictionaries and create compatibility agent

## 📝 License

This project was created for educational purposes as part of the "5-Day AI Agents Intensive" course.

## 🙏 Acknowledgments

Built with:
- Google Agent Development Kit (ADK)
- Gemini API
- FastAPI
- Google Cloud Run
