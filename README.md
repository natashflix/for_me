# **FOR ME — Personalized Ingredient Intelligence**

A production-grade multi-agent system for real-world compatibility analysis.

---

## The Moment That Inspired This Project

Most people genuinely try to choose the right product — but ingredient lists make that nearly impossible.

A person buys a "gentle" cream… only to discover hidden drying alcohols halfway down the INCI list.

Someone picks a "clean" protein bar… and misses the tiny "may contain traces of nuts" line hidden in the folds of the packaging.

Someone with curly hair uses a shampoo "for all hair types"… and winds up with dry, stripped strands because the formula is full of sulfates.

Someone buys a dish soap marketed as "safe for sensitive skin"… but reacts immediately to a buried preservative.

**No one made a bad decision.**

The information people need is there — just not in a form designed for humans.

---

## What FOR ME Does

FOR ME transforms ingredient lists from **food, cosmetics, and household products** into a personalized **FOR ME Score (0–100)** with clear, rule-based explanations.

It turns raw, inconsistent, multilingual ingredient text into:

* a personalized compatibility score
* transparent, reproducible reasoning
* ingredient-level insights
* strictly non-medical recommendations

FOR ME does **not** analyze diseases, symptoms, or treatments. It is a **consumer safety & compatibility agent**, not a medical system.

---

## Multimodal Input (Already Supported)

Users can:

* **paste ingredient text**, or
* **upload a product photo** — FOR ME extracts ingredients via **Gemini Vision OCR**.

Both inputs run through the same multi-agent pipeline.

---

## Mission

FOR ME exists to protect people from hidden risks in everyday products — cosmetics, food, and household chemicals.

It makes personalized, safe decisions possible **in seconds** for people with allergies, sensitivities, and ingredient-related reactions.

---

## Why Ingredient Lists Are Hard

Ingredient lists are:

* long
* multilingual
* inconsistent
* full of synonyms and chemical naming variations
* written for regulatory compliance, not for consumers

And yet, consumers must make personal choices based on them.

---

## Why This Matters

Manual ingredient checking usually takes **5–12 minutes per product**, and people still miss small-print risks: allergens, irritants, preservatives, surfactants, sugar alcohols, fragrances.

**FOR ME reduces this process to <1 second**, using:

* deterministic scoring,
* rule-based risk detection,
* personal constraints,
* robust QA validation.

**From 5–12 minutes → to <1 second.**

Marketing may promise "gentle" or "for all skin types," but compatibility is personal.

FOR ME reads what marketing doesn't say — and reveals whether a product is genuinely good *for you*.

---

## Why a Multi-Agent System?

Ingredient analysis is a **pipeline**, not a single task:

* multilingual parsing
* category detection
* constraint enforcement
* deterministic scoring
* safety routing
* explanation generation
* personalization & memory

One LLM cannot handle all of this reliably, consistently, and safely.

A multi-agent system ensures:

* separation of responsibilities  
* deterministic rule enforcement  
* transparent reasoning  
* medical safety boundaries  
* modularity & extensibility

---

## Architecture

### **High-Level Flow**

```
User Input → Orchestrator → Profile Manager → Domain Agent → Scoring Engine → Explainer Agent → Profile Update
```

### **Agent Team**

#### **Orchestrator**

* Detects intent (analysis / onboarding / update)
* Identifies category (food / cosmetics / household)
* Routes through the deterministic pipeline
* Assembles the final output

#### **Profile Manager**

* Loads allergies, sensitivities, user constraints
* Manages short-term memory (non-medical reactions)
* Enforces domain-specific rules

#### **Domain Compatibility Agents**

Each domain uses its own logic and risk dictionaries.

* **Food Agent:** allergens, traces, additives, sugar alcohols
* **Cosmetics Agent:** fragrances, preservatives, surfactants, alcohols
* **Household Agent:** irritants, solvents, surfactants

#### **Explainer Agent**

Turns structured scoring into human-friendly output.

Supports three explanation modes:

1. **Short Summary** — one-sentence insight
2. **Detailed Breakdown** — bullet points for risks & triggers
3. **Technical View** — structured, rule-based scoring trace

#### **Profile Update Agent**

Learns non-medical feedback such as:

* "Made my skin feel tight"
* "This snack upset my stomach"

Used only to adjust user constraints.

---

## Ingredient QA Loop (Hallucination Control)

Before scoring, FOR ME performs a QA pass:

* detects duplicate ingredients
* flags unknown tokens
* cross-checks all ingredients against user allergies & sensitivities
* applies domain-specific risk rules

This reduces hallucinations and ensures robust, deterministic scoring.

---

## How the FOR ME Score Works

### **Component Scores**

* **Safety (0–100)** — strict avoidances, allergens, critical risks
* **Sensitivity (0–100)** — irritants, reactives, "prefer-avoid" lists
* **Match (0–100)** — beneficial ingredients and personal goals

### **Domain Weighting**

| Domain    | Safety | Sensitivity | Match | Rationale                             |
| --------- | ------ | ----------- | ----- | ------------------------------------- |
| Food      | 50%    | 30%         | 20%   | Allergens can be dangerous            |
| Cosmetics | 30%    | 30%         | 40%   | "Does this fit your hair/skin goals?" |
| Household | 40%    | 30%         | 30%   | Safety + effectiveness                |

### **Final Score**

```
FOR ME Score = (Safety × weight) + (Sensitivity × weight) + (Match × weight)
```

### **Safety-First Rule**

Strict allergens **cap the maximum score at 15/100**, ensuring a safety-first approach.

---

## Non-Medical Safety

If user input contains medical content (symptoms, diagnoses, treatments):

* analysis stops
* the system triggers **Safety Redirect**
* FOR ME gives a safe, general response

Enforced through:

* orchestrator
* agent instructions
* response templates
* safety filters

---

## End-to-End Workflow

1. User inputs text or uploads a label photo
2. OCR extracts the ingredient list
3. Orchestrator detects intent & category
4. Parser normalizes multilingual ingredients
5. QA Loop validates the ingredient list
6. Domain Agent applies risk rules
7. Scoring Engine calculates compatibility
8. Explainer formats output in the chosen mode
9. Profile Update adjusts user constraints

Simple for the user.

Complex under the hood.

Fully transparent.

---

## Tech Stack

* **LLM / Agents:** Gemini 2.5 Flash Lite + Google ADK
* **Backend:** FastAPI
* **Tools:** Ingredient parser, risk dictionary, category detection, OCR
* **Memory:** Long-term & short-term personalization
* **Deployment:** Docker + Google Cloud Run
* **Observability:** Structured logging, metrics, tracing

---

## Quick Start

### Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure API Key

```bash
cp .env.example .env
```

Add your key:

```
GOOGLE_API_KEY=your-key
```

Get API key: https://aistudio.google.com/app/api-keys

> **Important**: Never commit `.env` file to git! It's already in `.gitignore`.

### Run the Server

```bash
python main.py
```

Server runs at: [http://localhost:8080](http://localhost:8080)

### Test It

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

**For complete API documentation, see [API_REFERENCE.md](./API_REFERENCE.md)**

---

## API Endpoints

* **POST /chat** — main endpoint (requires `X-User-Id`)
* **POST /analyze** — legacy analysis
* **POST /onboarding** — profile collection
* **POST /chat/upload** — OCR image upload
* **GET /health** — health check

### Example Request

```bash
POST /chat
Headers:
  X-User-Id: user_001
Body:
{
  "message": "Analyze this product",
  "ingredient_text": "aqua, glycerin, fragrance, parabens",
  "product_domain": "cosmetics"
}
```

### Example Response

```json
{
  "status": "success",
  "score": 45,
  "category": "cosmetics",
  "intent": "PRODUCT_ANALYSIS",
  "issues": [
    "Contains fragrance, which you've marked as a sensitivity",
    "Contains parabens, which may cause reactions"
  ],
  "reply": "This product has a FOR ME Score of 45/100. It contains fragrance and parabens, which may not be suitable for your sensitive skin profile."
}
```

---

## Project Structure

```
src/
  system.py               # Main system orchestrator
  memory.py               # Long-term/short-term memory
  observability.py        # Logging and metrics
  eval.py                 # Quality evaluation
  types.py                # Type definitions
  
  agents/
    orchestrator_agent.py      # Main coordinator
    onboarding_agent.py         # Profile collection
    profile_agent.py           # Profile management
    profile_update_agent.py    # Reaction learning
    food_compatibility_agent.py
    cosmetics_compatibility_agent.py
    household_compatibility_agent.py
    explainer_agent.py
    category_tools.py
    
  tools/
    ingredient_parser.py
    risk_dictionary.py
    category_dictionaries.py
    image_ocr.py

main.py                   # FastAPI entrypoint
tests/                    # Unit and integration tests
docs/                     # Architecture documentation
```

---

## Documentation

* **[API Reference](./API_REFERENCE.md)** - Complete API documentation
* **[Architecture](./docs/ARCHITECTURE.md)** - Detailed system design
* **[Architecture Diagrams](./docs/ARCHITECTURE_DIAGRAM.md)** - Mermaid diagrams
* **[Image Upload Guide](./docs/IMAGE_UPLOAD_GUIDE.md)** - OCR feature guide
* **[Unit Tests](./tests/README.md)** - Test suite documentation
* **[Example Notebook](./kaggle_notebook_example.py)** - Demo notebook with QA loop, multi-variant explanations, and result export (JSON/CSV)

---

## Testing

```bash
# Run evaluation suite
python -m src.eval

# Run API tests (start server first)
python main.py
# In another terminal:
python test_api.py

# Run bot tests
python test_bot.py

# Run unit tests with coverage
pytest tests/ --cov=src --cov-report=html
```

---

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

---

## Course Concepts Demonstrated

* Multi-agent orchestration
* Agent-as-a-Tool (A2A)
* Custom Tools
* Memory (long-term & short-term)
* Context engineering
* Observability
* Deployment on Cloud Run
* TypedDict / type safety

---

## Competition Fit — Concierge Agents

FOR ME solves the core question of the category:

**"Is this product good for *me*?"**

And demonstrates:

* multi-agent routing
* tool use
* deterministic rules
* explainability
* safety governance
* memory
* deployment

Perfect match.

---

## Final Thought

Most people don't read ingredient lists.

Not because they don't care — but because the information wasn't designed for them.

**FOR ME reads it for you.

And offers something no label ever does: clarity, personalized.**

---

## License

This project was created for educational purposes as part of the "5-Day AI Agents Intensive" course.

---

## Acknowledgments

Built with:

* Google Agent Development Kit (ADK)
* Gemini API
* FastAPI
* Google Cloud Run

---

*Built with love for the 5-Day AI Agents Intensive Capstone*
