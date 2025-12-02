# FOR ME System - Architecture Diagram

## 🏗️ Complete System Architecture

### Horizontal Layout (for presentations)

```mermaid
graph LR
    U[User] --> API[FastAPI]
    API --> EP1[/chat]
    API --> EP2[/upload]
    EP1 --> SYS[System]
    EP2 --> OCR[OCR]
    OCR --> EP1
    EP2 --> SYS
    SYS --> ORCH[Orchestrator]
    SYS --> SESS[Session]
    ORCH --> INT[Intent]
    INT --> PROF{Profile?}
    PROF -->|No| ONB[Onboarding]
    PROF -->|Yes| CAT[Category]
    CAT --> PARSE[Parse]
    PARSE --> CATEG{Type?}
    CATEG -->|food| FOOD[Food]
    CATEG -->|cosmetics| COSM[Cosmetics]
    CATEG -->|household| HOUSE[Household]
    FOOD --> RISKS[Risks]
    COSM --> RISKS
    HOUSE --> RISKS
    RISKS --> CTX[Context]
    CTX --> SCORE[Scoring]
    SCORE --> SAFE[Safety]
    SCORE --> SENS[Sensitivity]
    SCORE --> MATCH[Match]
    SAFE --> FINAL[FOR ME Score]
    SENS --> FINAL
    MATCH --> FINAL
    ORCH --> MEM[Memory]
    FOOD --> MEM
    COSM --> MEM
    HOUSE --> MEM
    ONB --> MEM
    ORCH --> GEM[Gemini]
    ONB --> GEM
    FINAL --> RESP[Response]
    RESP --> U
    
    classDef user fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef api fill:#fff4e1,stroke:#e65100,stroke-width:2px
    classDef core fill:#ffe1f5,stroke:#880e4f,stroke-width:3px
    classDef agent fill:#e1ffe1,stroke:#1b5e20,stroke-width:2px
    classDef tool fill:#e1e1ff,stroke:#0d47a1,stroke-width:2px
    classDef memory fill:#fff9e1,stroke:#f57f17,stroke-width:2px
    classDef external fill:#f5e1ff,stroke:#4a148c,stroke-width:2px
    classDef output fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    
    class U user
    class API,EP1,EP2 api
    class SYS,ORCH,INT core
    class ONB,FOOD,COSM,HOUSE agent
    class PARSE,RISKS,CAT,CTX,SCORE tool
    class MEM,SESS memory
    class GEM,OCR external
    class FINAL,RESP output
```

### Vertical Layout (for documentation)

```mermaid
graph TB
    U[User] --> API[FastAPI]
    API --> EP1[/chat]
    API --> EP2[/upload]
    EP1 --> SYS[System]
    EP2 --> OCR[OCR]
    OCR --> EP1
    EP2 --> SYS
    SYS --> ORCH[Orchestrator]
    SYS --> SESS[Session]
    ORCH --> INT[Intent]
    INT --> PROF{Profile?}
    PROF -->|No| ONB[Onboarding]
    PROF -->|Yes| CAT[Category]
    CAT --> PARSE[Parse]
    PARSE --> CATEG{Type?}
    CATEG -->|food| FOOD[Food]
    CATEG -->|cosmetics| COSM[Cosmetics]
    CATEG -->|household| HOUSE[Household]
    FOOD --> RISKS[Risks]
    COSM --> RISKS
    HOUSE --> RISKS
    RISKS --> CTX[Context]
    CTX --> SCORE[Scoring]
    SCORE --> SAFE[Safety]
    SCORE --> SENS[Sensitivity]
    SCORE --> MATCH[Match]
    SAFE --> FINAL[FOR ME Score]
    SENS --> FINAL
    MATCH --> FINAL
    ORCH --> MEM[Memory]
    FOOD --> MEM
    COSM --> MEM
    HOUSE --> MEM
    ONB --> MEM
    ORCH --> GEM[Gemini]
    ONB --> GEM
    FINAL --> RESP[Response]
    RESP --> U
    
    classDef user fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef api fill:#fff4e1,stroke:#e65100,stroke-width:2px
    classDef core fill:#ffe1f5,stroke:#880e4f,stroke-width:3px
    classDef agent fill:#e1ffe1,stroke:#1b5e20,stroke-width:2px
    classDef tool fill:#e1e1ff,stroke:#0d47a1,stroke-width:2px
    classDef memory fill:#fff9e1,stroke:#f57f17,stroke-width:2px
    classDef external fill:#f5e1ff,stroke:#4a148c,stroke-width:2px
    classDef output fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    
    class U user
    class API,EP1,EP2 api
    class SYS,ORCH,INT core
    class ONB,FOOD,COSM,HOUSE agent
    class PARSE,RISKS,CAT,CTX,SCORE tool
    class MEM,SESS memory
    class GEM,OCR external
    class FINAL,RESP output
```

## 📋 Component Legend

- **U**: User
- **API**: FastAPI Server
- **EP1**: POST /chat
- **EP2**: POST /chat/upload
- **SYS**: ForMeSystem
- **ORCH**: OrchestratorAgent
- **INT**: detect_intent
- **PROF**: Profile Check
- **ONB**: OnboardingAgent
- **CAT**: detect_product_category
- **PARSE**: parse_ingredients
- **CATEG**: Category Decision
- **FOOD**: FoodCompatibilityAgent
- **COSM**: CosmeticsCompatibilityAgent
- **HOUSE**: HouseholdCompatibilityAgent
- **RISKS**: get_ingredient_risks
- **CTX**: build_X_context
- **SCORE**: calculate_X_scores
- **SAFE**: Safety Score
- **SENS**: Sensitivity Score
- **MATCH**: Match Score
- **FINAL**: FOR ME Score
- **MEM**: Long-Term Memory
- **SESS**: Session Service
- **GEM**: Gemini API
- **OCR**: Image OCR
- **RESP**: Final Response

## 🔄 Key Flow

**Horizontal**: User → FastAPI → System → Orchestrator → Intent → Category → Agent → Tools → Scoring → Response → User

**Vertical**: User ↓ FastAPI ↓ System ↓ Orchestrator ↓ Intent ↓ Category ↓ Agent ↓ Tools ↓ Scoring ↓ Response ↓ User

---

**Copy the Mermaid code above and paste it into [Mermaid Live Editor](https://mermaid.live/) to view the interactive diagrams!**

**Both layouts are optimized for rendering! 🎯**
