"""
Risk Dictionary Tool

Maps ingredient names to risk tags (allergens, irritants, etc.).
"""

from typing import Dict, List, Set
from google.adk.tools.tool_context import ToolContext


# Risk dictionary: maps ingredient names to risk tags
RISK_DICTIONARY = {
    # Allergens
    "yellow-5": ["allergen", "food_coloring"],
    "желтый-5": ["allergen", "food_coloring"],
    "yellow-6": ["allergen", "food_coloring"],
    "red-40": ["allergen", "food_coloring"],
    "красный-40": ["allergen", "food_coloring"],
    "blue-1": ["allergen", "food_coloring"],
    "tartrazine": ["allergen", "food_coloring"],
    "carmine": ["allergen", "cochineal"],
    "cochineal": ["allergen"],
    "soy": ["allergen", "soy"],
    "соя": ["allergen", "soy"],
    "soybean": ["allergen", "soy"],
    "peanut": ["allergen", "peanut"],
    "peanuts": ["allergen", "peanut"],
    "tree nuts": ["allergen", "tree_nuts"],
    "almond": ["allergen", "tree_nuts"],
    "walnut": ["allergen", "tree_nuts"],
    "cashew": ["allergen", "tree_nuts"],
    "milk": ["allergen", "dairy"],
    "молоко": ["allergen", "dairy"],
    "молочные": ["allergen", "dairy"],
    "молочных": ["allergen", "dairy"],
    "производные молока": ["allergen", "dairy"],
    "производные": ["allergen", "dairy"],  # if in context of milk
    "lactose": ["allergen", "dairy"],
    "whey": ["allergen", "dairy"],
    "casein": ["allergen", "dairy"],
    "egg": ["allergen", "egg"],
    "eggs": ["allergen", "egg"],
    "gluten": ["allergen", "gluten"],
    "глютен": ["allergen", "gluten"],
    "wheat": ["allergen", "gluten"],
    "пшеничная": ["allergen", "gluten"],
    "пшеницы": ["allergen", "gluten"],
    "мука пшеничная": ["allergen", "gluten"],
    "barley": ["allergen", "gluten"],
    "rye": ["allergen", "gluten"],
    "nickel": ["allergen", "metal"],
    "fragrance": ["fragrance", "irritant"],
    "parfum": ["fragrance", "irritant"],
    "perfume": ["fragrance", "irritant"],
    
    # Drying alcohols
    "alcohol": ["drying_alcohol"],
    "alcohol denat": ["drying_alcohol"],
    "denatured alcohol": ["drying_alcohol"],
    "ethanol": ["drying_alcohol"],
    "isopropyl alcohol": ["drying_alcohol"],
    "sd alcohol": ["drying_alcohol"],
    "sd alcohol 40": ["drying_alcohol"],
    
    # Harsh surfactants
    "sodium lauryl sulfate": ["harsh_surfactant", "sls"],
    "sls": ["harsh_surfactant", "sls"],
    "sodium laureth sulfate": ["harsh_surfactant", "sles"],
    "sles": ["harsh_surfactant", "sles"],
    "ammonium lauryl sulfate": ["harsh_surfactant"],
    
    # High salt content
    "sodium chloride": ["high_salt"],
    "salt": ["high_salt"],
    "соль": ["high_salt"],
    "sodium": ["high_salt"],
    "натрия": ["high_salt"],
    
    # Preservatives (can be irritants)
    "parabens": ["preservative", "potential_irritant"],
    "methylparaben": ["preservative", "potential_irritant"],
    "propylparaben": ["preservative", "potential_irritant"],
    "formaldehyde": ["preservative", "irritant"],
    "formaldehyde releaser": ["preservative", "irritant"],
    "консерванты": ["preservative", "potential_irritant"],
    "preservatives": ["preservative", "potential_irritant"],
    
    # Acids (can be harsh)
    "glycolic acid": ["acid", "potential_irritant"],
    "salicylic acid": ["acid", "potential_irritant"],
    "lactic acid": ["acid", "potential_irritant"],
    "citric acid": ["acid"],
    
    # Flavor enhancers (Russian)
    "усилители вкуса": ["flavor_enhancer", "potential_irritant"],
    "усилитель вкуса": ["flavor_enhancer", "potential_irritant"],
    "глутамат натрия": ["flavor_enhancer", "potential_irritant"],
    "инозинат натрия": ["flavor_enhancer", "potential_irritant"],
    "гуанилат натрия": ["flavor_enhancer", "potential_irritant"],
    "msg": ["flavor_enhancer", "potential_irritant"],
    
    # Soy derivatives
    "гидролизованный растительный белок": ["soy", "allergen"],
    "гидролизованный белок": ["soy", "allergen"],
    
    # Beneficial ingredients (negative risk tags for scoring)
    "glycerin": ["hydrating", "beneficial"],
    "glycerol": ["hydrating", "beneficial"],
    "hyaluronic acid": ["hydrating", "beneficial"],
    "ceramides": ["hydrating", "beneficial"],
    "squalane": ["hydrating", "beneficial"],
    "dimethicone": ["silicone", "beneficial"],
    "cyclomethicone": ["silicone", "beneficial"],
    "silicone": ["silicone", "beneficial"],
}


def get_ingredient_risks(tool_context: ToolContext, ingredients: List[str]) -> Dict[str, any]:
    """
    Maps a list of normalized ingredient names to their risk tags.
    
    This tool looks up each ingredient in the risk dictionary and returns
    a mapping of ingredient -> list of risk tags.
    
    Args:
        tool_context: ADK tool context
        ingredients: List of normalized ingredient names (lowercase, cleaned).
    
    Returns:
        Dictionary with status and risk mapping.
        Success: {
            "status": "success",
            "risks": {
                "ingredient1": ["risk1", "risk2", ...],
                "ingredient2": ["risk3", ...],
            },
            "all_risk_tags": ["risk1", "risk2", ...]  # unique set
        }
        Error: {"status": "error", "error_message": "..."}
    """
    try:
        if not ingredients:
            return {
                "status": "error",
                "error_message": "Empty ingredients list provided"
            }
        
        risks = {}
        all_tags = set()
        
        for ingredient in ingredients:
            # Direct lookup
            ingredient_lower = ingredient.lower().strip()
            
            # Check for exact match
            if ingredient_lower in RISK_DICTIONARY:
                tags = RISK_DICTIONARY[ingredient_lower]
                risks[ingredient] = tags
                all_tags.update(tags)
            else:
                # Partial match: check if ingredient contains any key
                # (e.g., "sodium lauryl sulfate" contains "sls")
                found_tags = []
                for key, tags in RISK_DICTIONARY.items():
                    if key in ingredient_lower or ingredient_lower in key:
                        found_tags.extend(tags)
                
                if found_tags:
                    # Deduplicate
                    risks[ingredient] = list(set(found_tags))
                    all_tags.update(found_tags)
                else:
                    # No risks found for this ingredient
                    risks[ingredient] = []
        
        return {
            "status": "success",
            "risks": risks,
            "all_risk_tags": sorted(list(all_tags)),
            "ingredients_with_risks": len([i for i, tags in risks.items() if tags]),
            "total_ingredients": len(ingredients)
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Risk lookup error: {str(e)}"
        }

