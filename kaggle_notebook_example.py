"""
FOR ME - Example Notebook for Kaggle Writeup
Demonstrates product analysis, QA loop, and result export
"""

import json
import csv
import asyncio
from typing import Dict, List, Any
from datetime import datetime

# Import FOR ME system components
from src.system import ForMeSystem
from src.tools.ingredient_parser import parse_ingredients
from google.adk.tools.tool_context import SimpleContext


# Example products to analyze
EXAMPLE_PRODUCTS = [
    {
        "product_name": "Gentle Hydrating Face Cream",
        "category": "cosmetics",
        "ingredient_text": "Aqua, Glycerin, Dimethicone, Fragrance, Parabens, Alcohol Denat"
    },
    {
        "product_name": "Protein Energy Bar",
        "category": "food",
        "ingredient_text": "Dates, Almonds, Peanuts, Whey Protein, Soy Lecithin, Natural Flavors"
    },
    {
        "product_name": "All-Purpose Cleaner",
        "category": "household",
        "ingredient_text": "Water, Sodium Lauryl Sulfate, Citric Acid, Fragrance, Preservatives"
    },
    {
        "product_name": "Sensitive Skin Shampoo",
        "category": "cosmetics",
        "ingredient_text": "Water, Cocamidopropyl Betaine, Glycerin, Aloe Vera, Chamomile Extract"
    },
    {
        "product_name": "Organic Snack Mix",
        "category": "food",
        "ingredient_text": "Organic Cashews, Organic Almonds, Organic Raisins, Sea Salt"
    }
]

# Example user profile
EXAMPLE_PROFILE = {
    "allergies": ["peanuts", "soy"],
    "avoid_categories": ["fragrance", "parabens"],
    "avoid_ingredients": ["sodium lauryl sulfate", "alcohol denat"],
    "prefer_avoid": [
        {"ingredient": "sulfates", "type": "preference"},
        {"ingredient": "alcohol", "type": "preference"}
    ],
    "strict_avoid": [
        {"ingredient": "peanuts", "type": "allergen"},
        {"ingredient": "soy", "type": "allergen"}
    ],
    "goals": ["hydrating", "sensitive skin friendly"]
}


def format_explanation_modes(result: Dict[str, Any], category: str) -> Dict[str, str]:
    """
    Formats result into different explanation modes.
    
    Returns:
        Dictionary with short_summary, detailed_breakdown, technical_view
    """
    score = result.get("for_me_score", 0)
    safety_score = result.get("safety_score", 0)
    sensitivity_score = result.get("sensitivity_score", 0)
    match_score = result.get("match_score", 0)
    
    risk_analysis = result.get("risk_analysis", {})
    from_profile = risk_analysis.get("from_profile_match", [])
    generic_risks = risk_analysis.get("generic_risks", [])
    
    # Short Summary
    if score >= 70:
        summary_short = f"Good match (Score: {score}/100). Suitable for your profile."
    elif score >= 40:
        summary_short = f"Moderate match (Score: {score}/100). Some concerns detected."
    else:
        summary_short = f"Poor match (Score: {score}/100). Significant risks identified."
    
    if from_profile:
        main_issue = from_profile[0].get("ingredient", "unknown")
        summary_short += f" Contains {main_issue}."
    
    # Detailed Breakdown
    breakdown_parts = [
        f"FOR ME Score: {score}/100",
        f"Safety: {safety_score}/100 | Sensitivity: {sensitivity_score}/100 | Match: {match_score}/100",
        ""
    ]
    
    if from_profile:
        breakdown_parts.append("⚠️ Profile-Specific Risks:")
        for risk in from_profile[:5]:  # Top 5
            breakdown_parts.append(f"  • {risk.get('ingredient', 'unknown')}: {risk.get('reason', '')}")
        breakdown_parts.append("")
    
    if generic_risks:
        breakdown_parts.append("ℹ️ General Risk Factors:")
        for risk in generic_risks[:3]:  # Top 3
            breakdown_parts.append(f"  • {risk.get('ingredient', 'unknown')}: {risk.get('reason', '')}")
    
    summary_detailed = "\n".join(breakdown_parts)
    
    # Technical View
    technical_parts = [
        f"Category: {category.upper()}",
        f"Component Scores:",
        f"  Safety: {safety_score}/100 (weight: {get_category_weight(category, 'safety')})",
        f"  Sensitivity: {sensitivity_score}/100 (weight: {get_category_weight(category, 'sensitivity')})",
        f"  Match: {match_score}/100 (weight: {get_category_weight(category, 'match')})",
        f"",
        f"Final Score Calculation:",
        f"  FOR ME = ({safety_score} × {get_category_weight(category, 'safety')}) + "
        f"({sensitivity_score} × {get_category_weight(category, 'sensitivity')}) + "
        f"({match_score} × {get_category_weight(category, 'match')}) = {score}",
        f"",
        f"Risk Analysis:",
        f"  Profile-matched risks: {len(from_profile)}",
        f"  Generic risks: {len(generic_risks)}"
    ]
    
    summary_technical = "\n".join(technical_parts)
    
    return {
        "summary_short": summary_short,
        "summary_detailed": summary_detailed,
        "summary_technical": summary_technical
    }


def get_category_weight(category: str, score_type: str) -> float:
    """Returns category-specific weight for score type."""
    weights = {
        "food": {"safety": 0.5, "sensitivity": 0.3, "match": 0.2},
        "cosmetics": {"safety": 0.3, "sensitivity": 0.3, "match": 0.4},
        "household": {"safety": 0.4, "sensitivity": 0.3, "match": 0.3}
    }
    return weights.get(category, {"safety": 0.33, "sensitivity": 0.33, "match": 0.34}).get(score_type, 0.33)


async def analyze_products_with_qa(system: ForMeSystem, user_id: str = "notebook_user") -> List[Dict[str, Any]]:
    """
    Analyzes products with QA loop checks.
    
    Returns:
        List of analysis results with QA metadata
    """
    results = []
    
    for product in EXAMPLE_PRODUCTS:
        print(f"\n📦 Analyzing: {product['product_name']}")
        
        # Step 1: Parse ingredients (includes QA: duplicates, unknown detection)
        tool_context = SimpleContext({})
        parse_result = parse_ingredients(
            tool_context=tool_context,
            ingredient_text=product["ingredient_text"]
        )
        
        if parse_result["status"] != "success":
            print(f"  ❌ Parsing failed: {parse_result.get('error_message')}")
            continue
        
        ingredients = parse_result["ingredients"]
        qa_metadata = parse_result.get("qa_metadata", {})
        
        print(f"  ✓ Parsed {len(ingredients)} ingredients")
        if qa_metadata.get("duplicates_removed"):
            print(f"  ⚠️ Removed {len(qa_metadata['duplicates_removed'])} duplicates")
        if qa_metadata.get("unknown_ingredients"):
            print(f"  ⚠️ Flagged {len(qa_metadata['unknown_ingredients'])} unknown tokens")
        
        # Step 2: Analyze product through system
        try:
            result = await system.analyze_product(
                user_id=user_id,
                ingredient_text=product["ingredient_text"],
                product_domain=product["category"],
                skip_onboarding=True  # Use existing profile
            )
            
            # Step 3: Format explanation modes
            explanations = format_explanation_modes(result, product["category"])
            
            # Step 4: Count high-risk ingredients
            risk_analysis = result.get("risk_analysis", {})
            from_profile = risk_analysis.get("from_profile_match", [])
            generic_risks = risk_analysis.get("generic_risks", [])
            high_risk_count = len(from_profile) + len([r for r in generic_risks if "high" in str(r).lower()])
            
            # Check for allergy flags
            allergy_flag = any(
                "allergen" in str(risk).lower() or 
                "peanut" in str(risk).lower() or 
                "soy" in str(risk).lower()
                for risk in from_profile
            )
            
            analysis_result = {
                "product_name": product["product_name"],
                "category": product["category"],
                "ingredient_text": product["ingredient_text"],
                "ingredients_parsed": ingredients,
                "qa_metadata": qa_metadata,
                "for_me_score": result.get("for_me_score", 0),
                "safety_score": result.get("safety_score", 0),
                "sensitivity_score": result.get("sensitivity_score", 0),
                "match_score": result.get("match_score", 0),
                "high_risk_count": high_risk_count,
                "allergy_flag": allergy_flag,
                "risk_analysis": risk_analysis,
                "explanations": explanations,
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(analysis_result)
            print(f"  ✓ Score: {result.get('for_me_score', 0)}/100")
            
        except Exception as e:
            print(f"  ❌ Analysis failed: {str(e)}")
            continue
    
    return results


def export_results_to_json(results: List[Dict[str, Any]], filename: str = "for_me_results.json"):
    """Export full results to JSON."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Exported full results to {filename}")


def export_summary_to_csv(results: List[Dict[str, Any]], filename: str = "for_me_summary.csv"):
    """Export summary table to CSV."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "product_name", "category", "score", "high_risk_count", "allergy_flag"
        ])
        writer.writeheader()
        for result in results:
            writer.writerow({
                "product_name": result["product_name"],
                "category": result["category"],
                "score": result["for_me_score"],
                "high_risk_count": result["high_risk_count"],
                "allergy_flag": result["allergy_flag"]
            })
    print(f"💾 Exported summary to {filename}")


async def main():
    """
    Main notebook execution.
    
    This demonstrates:
    1. Product analysis with QA loop
    2. Multi-variant explanation formatting
    3. Result export (JSON + CSV)
    """
    print("=" * 60)
    print("FOR ME - Product Analysis Notebook")
    print("=" * 60)
    
    # Initialize system
    system = ForMeSystem()
    
    # Setup user profile (in real scenario, this would come from onboarding)
    # For demo, we'll set it in session state
    from src.memory import SessionService
    session_service = SessionService()
    session = await session_service.create_session(
        app_name=system.app.name,
        user_id="notebook_user",
        session_id="notebook_session"
    )
    profile_key = "user:notebook_user:long_profile"
    session.state[profile_key] = EXAMPLE_PROFILE
    
    print(f"\n👤 User Profile Loaded:")
    print(f"   Allergies: {EXAMPLE_PROFILE.get('allergies', [])}")
    print(f"   Avoid: {EXAMPLE_PROFILE.get('avoid_categories', [])}")
    
    # Analyze products
    print(f"\n🔍 Analyzing {len(EXAMPLE_PRODUCTS)} products...")
    results = await analyze_products_with_qa(system, user_id="notebook_user")
    
    # Display example explanations
    if results:
        print("\n" + "=" * 60)
        print("📊 Example: Multi-Variant Explanations")
        print("=" * 60)
        example = results[0]
        print(f"\nProduct: {example['product_name']}")
        print(f"\n--- Short Summary ---")
        print(example["explanations"]["summary_short"])
        print(f"\n--- Detailed Breakdown ---")
        print(example["explanations"]["summary_detailed"])
        print(f"\n--- Technical View ---")
        print(example["explanations"]["summary_technical"])
    
    # Export artifacts for reproducibility
    # These files demonstrate how FOR ME could log and share results with other systems.
    export_results_to_json(results)
    export_summary_to_csv(results)
    
    print("\n" + "=" * 60)
    print("✅ Notebook execution complete!")
    print("=" * 60)
    print("\nGenerated artifacts:")
    print("  • for_me_results.json - Full analysis results")
    print("  • for_me_summary.csv - Summary table for quick review")


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())

