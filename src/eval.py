"""
Agent Quality Evaluation System

Eval dataset with test cases for each category.
Implements quality flywheel for regression testing.
"""

from typing import Dict, Any, List, Tuple
from src.system import ForMeSystem
from src.agents.category_tools import detect_product_category, analyze_food_product, analyze_cosmetics_product, analyze_household_product
from google.adk.sessions import InMemorySessionService


# ============================================================================
# EVAL DATASET
# ============================================================================

TEST_CASES = [
    # FOOD TEST CASES
    {
        "id": "food_001",
        "category": "food",
        "product_name": "Milka Chocolate",
        "ingredient_text": "Sugar, cocoa butter, cocoa paste, whole milk powder, dried milk whey, skimmed milk powder, milk fat, emulsifiers (soy lecithin, E 476), nut paste (hazelnut), flavoring.",
        "user_profile": {
            "food_strict_avoid": [
                {"ingredient": "hazelnut", "type": "allergen"},
                {"ingredient": "nuts", "type": "allergen"},
            ],
            "food_prefer_avoid": [
                {"ingredient": "sugar", "type": "preference"},
            ],
        },
        "expected": {
            "category": "food",
            "safety_score": 0,
            "final_cap": 15,
            "has_strict_allergen_explicit": True,
        },
    },
    {
        "id": "food_002",
        "category": "food",
        "product_name": "Halva (Sesame)",
        "ingredient_text": "Sesame seeds, isomalt, molasses.",
        "user_profile": {
            "food_strict_avoid": [
                {"ingredient": "nuts", "type": "allergen"},
            ],
            "food_prefer_avoid": [
                {"ingredient": "sugar", "type": "preference"},
            ],
        },
        "expected": {
            "category": "food",
            "safety_score": 100,
            "final_cap": 100,
            "has_strict_allergen_explicit": False,
        },
    },
    {
        "id": "food_003",
        "category": "food",
        "product_name": "Halva with Nuts",
        "ingredient_text": "dried milk, butter, sugar, alkalized cocoa powder, walnuts",
        "user_profile": {
            "food_strict_avoid": [
                {"ingredient": "walnuts", "type": "allergen"},
                {"ingredient": "nuts", "type": "allergen"},
            ],
        },
        "expected": {
            "category": "food",
            "safety_score": 0,
            "final_cap": 15,
            "has_strict_allergen_explicit": True,
        },
    },
    
    # COSMETICS TEST CASES
    {
        "id": "cosmetics_001",
        "category": "cosmetics",
        "product_name": "Shampoo with Fragrance",
        "ingredient_text": "AQUA / WATER / EAU • SODIUM LAURETH SULFATE • COCAMIDOPROPYL BETAINE • DIMETHICONE • SODIUM CHLORIDE • CITRIC ACID • HEXYLENE GLYCOL • SODIUM BENZOATE • SODIUM HYDROXIDE • AMODIMETHICONE • CARBOMER • GUAR HYDROXYPROPYLTRIMONIUM CHLORIDE • TRIDECETH-10 • GLYCERIN • SALICYLIC ACID • GLYCOL DISTEARATE • NIACINAMIDE • MICA • PEG-100 STEARATE • LINALOOL • STEARETH-6 • PHENOXYETHANOL • COCO-BETAINE • TRIDECETH-3 • CI 77891 / TITANIUM DIOXIDE • RESVERATROL • BENZYL ALCOHOL • ACETIC ACID • FUMARIC ACID • PARFUM / FRAGRANCE",
        "user_profile": {
            "cosmetics_sensitivities": ["fragrance", "parfum"],
            "hair_type": "curly",
            "hair_goals": ["hydration", "anti_frizz"],
        },
        "expected": {
            "category": "cosmetics",
            "safety_score": 100,  # Should NOT drop for irritants
            "sensitivity_score": "< 50",  # Should be affected
            "match_score": "> 60",  # Should have positives (glycerin, silicones)
        },
    },
    {
        "id": "cosmetics_002",
        "category": "cosmetics",
        "product_name": "Fragrance-Free Shampoo",
        "ingredient_text": "AQUA, GLYCERIN, DIMETHICONE, NIACINAMIDE, PANTHENOL, CERAMIDES",
        "user_profile": {
            "cosmetics_sensitivities": ["fragrance"],
            "hair_type": "curly",
            "hair_goals": ["hydration"],
        },
        "expected": {
            "category": "cosmetics",
            "safety_score": 100,
            "sensitivity_score": 100,
            "match_score": "> 70",
        },
    },
    
    # HOUSEHOLD TEST CASES
    {
        "id": "household_001",
        "category": "household",
        "product_name": "Bleach Cleaner",
        "ingredient_text": "SODIUM HYPOCHLORITE, WATER, SURFACTANTS, FRAGRANCE",
        "user_profile": {
            "household_strict_avoid": [
                {"ingredient": "bleach", "type": "toxic"},
                {"ingredient": "chlorine", "type": "toxic"},
            ],
        },
        "expected": {
            "category": "household",
            "safety_score": 0,
            "final_cap": 20,
        },
    },
    {
        "id": "household_002",
        "category": "household",
        "product_name": "Eco-Friendly Cleaner",
        "ingredient_text": "WATER, CITRIC ACID, ENZYMES, PLANT-BASED SURFACTANTS",
        "user_profile": {
            "household_sensitivities": ["fragrance"],
        },
        "expected": {
            "category": "household",
            "safety_score": 100,
            "match_score": "> 60",  # Should have positives
        },
    },
]


# ============================================================================
# EVALUATION FUNCTIONS
# ============================================================================

async def run_eval(
    system: ForMeSystem,
    test_cases: List[Dict[str, Any]] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Runs evaluation on test cases and prints metrics.
    
    Metrics:
    - Category accuracy
    - Correctness of final caps
    - Boundary violations (safety > cap, etc.)
    
    Args:
        system: ForMeSystem instance
        test_cases: List of test cases (defaults to TEST_CASES)
        verbose: Print detailed results
    
    Returns:
        Dictionary with evaluation metrics
    """
    if test_cases is None:
        test_cases = TEST_CASES
    
    session_service = InMemorySessionService()
    
    class SimpleContext:
        def __init__(self, state):
            self.state = state
    
    results = []
    metrics = {
        "total": len(test_cases),
        "category_correct": 0,
        "category_incorrect": 0,
        "safety_correct": 0,
        "safety_incorrect": 0,
        "final_cap_correct": 0,
        "final_cap_incorrect": 0,
        "boundary_violations": 0,
    }
    
    for test_case in test_cases:
        test_id = test_case["id"]
        expected = test_case["expected"]
        user_profile = test_case["user_profile"]
        
        # Setup session with profile
        session = await session_service.create_session(
            app_name=system.app.name,
            user_id=f"eval_user_{test_id}",
            session_id=f"eval_{test_id}",
        )
        
        # Set profile in state
        profile_key = f"user:eval_user_{test_id}:long_profile"
        session.state[profile_key] = user_profile
        
        tool_context = SimpleContext(session.state)
        
        # Detect category
        category_result = detect_product_category(
            tool_context=tool_context,
            ingredient_text=test_case["ingredient_text"],
            product_domain=test_case.get("category"),
        )
        detected_category = category_result.get("category")
        
        # Analyze product
        if detected_category == "food":
            result = analyze_food_product(
                tool_context=tool_context,
                user_id=f"eval_user_{test_id}",
                ingredient_text=test_case["ingredient_text"],
            )
        elif detected_category == "cosmetics":
            result = analyze_cosmetics_product(
                tool_context=tool_context,
                user_id=f"eval_user_{test_id}",
                ingredient_text=test_case["ingredient_text"],
            )
        elif detected_category == "household":
            result = analyze_household_product(
                tool_context=tool_context,
                user_id=f"eval_user_{test_id}",
                ingredient_text=test_case["ingredient_text"],
            )
        else:
            result = {"status": "error", "error_message": "Unknown category"}
        
        # Check category accuracy
        expected_category = expected.get("category")
        category_correct = detected_category == expected_category
        if category_correct:
            metrics["category_correct"] += 1
        else:
            metrics["category_incorrect"] += 1
        
        # Check safety score
        expected_safety = expected.get("safety_score")
        if expected_safety is not None:
            if isinstance(expected_safety, str):
                # Handle ranges like "> 50"
                if expected_safety.startswith(">"):
                    safety_correct = result.get("safety_score", 0) > int(expected_safety.split()[1])
                elif expected_safety.startswith("<"):
                    safety_correct = result.get("safety_score", 0) < int(expected_safety.split()[1])
                else:
                    safety_correct = False
            else:
                safety_correct = result.get("safety_score") == expected_safety
            
            if safety_correct:
                metrics["safety_correct"] += 1
            else:
                metrics["safety_incorrect"] += 1
        
        # Check final_cap
        expected_cap = expected.get("final_cap")
        if expected_cap is not None:
            cap_correct = result.get("final_cap") == expected_cap
            if cap_correct:
                metrics["final_cap_correct"] += 1
            else:
                metrics["final_cap_incorrect"] += 1
            
            # Check boundary violation
            for_me_score = result.get("for_me_score", 0)
            if for_me_score > expected_cap:
                metrics["boundary_violations"] += 1
        
        results.append({
            "test_id": test_id,
            "category_correct": category_correct,
            "result": result,
            "expected": expected,
        })
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"Test: {test_id} - {test_case['product_name']}")
            print(f"{'='*70}")
            print(f"Category: {detected_category} (expected: {expected_category}) {'✅' if category_correct else '❌'}")
            print(f"Safety Score: {result.get('safety_score')} (expected: {expected_safety})")
            print(f"Final Cap: {result.get('final_cap')} (expected: {expected_cap})")
            print(f"FOR ME Score: {result.get('for_me_score')}")
    
    # Calculate pass/fail
    total_tests = metrics["total"]
    category_accuracy = metrics["category_correct"] / total_tests if total_tests > 0 else 0.0
    boundary_violations = metrics["boundary_violations"]
    
    passed = (
        category_accuracy >= 0.85
        and boundary_violations == 0
    )
    
    # Calculate pass/fail
    total_tests = metrics["total"]
    category_accuracy = metrics["category_correct"] / total_tests if total_tests > 0 else 0.0
    boundary_violations = metrics["boundary_violations"]
    
    passed = (
        category_accuracy >= 0.85
        and boundary_violations == 0
    )
    
    # Print summary
    if verbose:
        print(f"\n{'='*70}")
        print("EVALUATION SUMMARY")
        print(f"{'='*70}")
        print(f"Total tests: {metrics['total']}")
        print(f"Category accuracy: {metrics['category_correct']}/{metrics['total']} ({100*category_accuracy:.1f}%)")
        print(f"Safety score correctness: {metrics['safety_correct']}/{metrics['safety_correct']+metrics['safety_incorrect']} ({100*metrics['safety_correct']/(metrics['safety_correct']+metrics['safety_incorrect'] or 1):.1f}%)")
        print(f"Final cap correctness: {metrics['final_cap_correct']}/{metrics['final_cap_correct']+metrics['final_cap_incorrect']} ({100*metrics['final_cap_correct']/(metrics['final_cap_correct']+metrics['final_cap_incorrect'] or 1):.1f}%)")
        print(f"Boundary violations: {metrics['boundary_violations']}")
        print(f"\n{'='*70}")
        print(f"QUALITY GATE: {'✅ PASSED' if passed else '❌ FAILED'}")
        print(f"{'='*70}\n")
    
    return {
        "passed": passed,
        "metrics": metrics,
        "results": results,
    }


if __name__ == "__main__":
    # Run evaluation
    import asyncio
    import sys
    
    async def main():
        system = ForMeSystem(use_persistent_storage=False)
        result = await run_eval(system, verbose=True)
        
        # Exit with error code if failed
        if not result.get("passed", False):
            print("\n❌ Evaluation FAILED - quality gate not passed")
            sys.exit(1)
        else:
            print("\n✅ Evaluation PASSED - quality gate passed")
            sys.exit(0)
    
    asyncio.run(main())

