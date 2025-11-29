# FOR ME Test Suite

## Overview

This directory contains unit tests for the FOR ME system. The tests are organized by component and cover core functionality without requiring external dependencies (like API keys).

## Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_memory.py       # Memory functions
│   ├── test_scoring.py      # Scoring functions (food, cosmetics, household)
│   ├── test_tools.py        # Tool functions (parsing, risk dictionary)
│   ├── test_context_builders.py  # Context builder functions
│   └── test_system_helpers.py   # System helper functions
└── integration/             # Integration tests (may require API keys)
```

## Running Tests

### Run all unit tests:
```bash
pytest tests/unit/ -v
```

### Run with coverage:
```bash
pytest tests/unit/ --cov=src --cov-report=html
```

### Run specific test file:
```bash
pytest tests/unit/test_memory.py -v
```

### Run specific test:
```bash
pytest tests/unit/test_memory.py::TestIsProfileMinimal::test_empty_profile_is_minimal -v
```

## Test Coverage

Current coverage: **34%** (986/1495 lines)

### Well-covered modules:
- `scoring_weights.py`: 100%
- `router_agent.py`: 100%
- `category_dictionaries.py`: 100%
- `cosmetics_compatibility_agent.py`: 84%
- `food_compatibility_agent.py`: 85%
- `household_compatibility_agent.py`: 78%
- `ingredient_parser.py`: 75%
- `risk_dictionary.py`: 81%

### Modules needing more coverage:
- `system.py`: 16% (integration tests needed)
- `scoring_agent.py`: 4% (integration tests needed)
- `observability.py`: 0% (integration tests needed)
- `eval.py`: 0% (integration tests needed)

## Test Categories

### Unit Tests (`tests/unit/`)

**Fast, isolated tests** that don't require:
- API keys
- External services
- Database connections
- Network access

**Coverage:**
- ✅ Memory functions (`is_profile_minimal`, `apply_repeated_reactions_to_scores`)
- ✅ Scoring functions (`calculate_food_scores`, `calculate_cosmetics_scores`, `calculate_household_scores`)
- ✅ Tool functions (`parse_ingredients`, `get_ingredient_risks`)
- ✅ Context builders (`build_food_context`, `build_cosmetics_context`, `build_household_context`)
- ✅ System helpers (`_is_profile_incomplete`)

### Integration Tests (`tests/integration/`)

**End-to-end tests** that may require:
- API keys (GOOGLE_API_KEY)
- External services
- Database connections

**Planned coverage:**
- Full system flow (onboarding → analysis → profile update)
- Agent-to-agent communication
- Session management
- Observability and logging

## Writing New Tests

### Example Unit Test:

```python
import pytest
from src.memory import is_profile_minimal

class TestIsProfileMinimal:
    def test_empty_profile_is_minimal(self, empty_profile):
        """Empty profile should be considered minimal."""
        assert is_profile_minimal(empty_profile) is True
```

### Using Fixtures:

```python
def test_food_scoring(self, sample_food_profile, sample_ingredients_list, sample_ingredient_risks):
    """Test food product scoring."""
    result = calculate_food_scores(
        profile=sample_food_profile,
        ingredient_risks=sample_ingredient_risks,
        ingredients_list=sample_ingredients_list,
    )
    assert result["status"] == "success"
```

## Fixtures

Available fixtures (defined in `conftest.py`):

- `empty_profile`: Empty user profile
- `sample_food_profile`: Sample food profile with allergies
- `sample_cosmetics_profile`: Sample cosmetics profile with sensitivities
- `sample_ingredient_risks`: Sample risk mappings
- `sample_ingredients_list`: Sample normalized ingredients list
- `mock_tool_context`: Mock ToolContext object

## Continuous Integration

Tests should be run:
- Before committing code
- In CI/CD pipeline
- Before deploying to production

## Coverage Goals

- **Current**: 34%
- **Target**: 70%+ (unit tests)
- **Stretch**: 85%+ (with integration tests)

