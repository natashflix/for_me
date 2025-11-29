"""
Category-specific dictionaries for product analysis.

Each category (FOOD, COSMETICS, HOUSEHOLD) has its own dictionaries
that are used ONLY by the corresponding compatibility agent.
"""

# ============================================================================
# FOOD DICTIONARIES - Strict rules for food products
# ============================================================================

FOOD_AVOID = {
    # Strictly avoided allergens
    "gluten": ["allergen", "gluten"],
    "глютен": ["allergen", "gluten"],
    "wheat": ["allergen", "gluten"],
    "пшеница": ["allergen", "gluten"],
    "soy": ["allergen", "soy"],
    "соя": ["allergen", "soy"],
    "soybean": ["allergen", "soy"],
    "milk": ["allergen", "dairy"],
    "молоко": ["allergen", "dairy"],
    "dairy": ["allergen", "dairy"],
    "lactose": ["allergen", "dairy"],
    "peanut": ["allergen", "peanut"],
    "peanuts": ["allergen", "peanut"],
    "tree nuts": ["allergen", "tree_nuts"],
    "nuts": ["allergen", "tree_nuts"],
    "орехи": ["allergen", "tree_nuts"],
    "walnut": ["allergen", "tree_nuts"],
    "грецкие орехи": ["allergen", "tree_nuts"],
    "hazelnut": ["allergen", "tree_nuts"],
    "фундук": ["allergen", "tree_nuts"],
    "almond": ["allergen", "tree_nuts"],
    "egg": ["allergen", "egg"],
    "eggs": ["allergen", "egg"],
    "yellow-5": ["allergen", "food_coloring"],
    "желтый-5": ["allergen", "food_coloring"],
    "tartrazine": ["allergen", "food_coloring"],
    "yellow 5": ["allergen", "food_coloring"],
}

FOOD_WARN = {
    # Moderate warnings
    "high_salt": ["high_salt", "sodium"],
    "высокая соль": ["high_salt", "sodium"],
    "salt": ["high_salt", "sodium"],
    "соль": ["high_salt", "sodium"],
    "sodium": ["high_salt", "sodium"],
    "sugar": ["high_sugar"],
    "сахар": ["high_sugar"],
    "sucrose": ["high_sugar"],
    "fructose": ["high_sugar"],
    "msg": ["flavor_enhancer", "msg"],
    "глутамат": ["flavor_enhancer", "msg"],
    "monosodium glutamate": ["flavor_enhancer", "msg"],
    "sweeteners": ["artificial_sweetener"],
    "подсластители": ["artificial_sweetener"],
    "aspartame": ["artificial_sweetener"],
    "saccharin": ["artificial_sweetener"],
}

FOOD_POSITIVE = {
    # Positive ingredients for food
    "fiber": ["fiber", "healthy"],
    "клетчатка": ["fiber", "healthy"],
    "protein": ["protein", "healthy"],
    "белок": ["protein", "healthy"],
    "vitamins": ["vitamins", "healthy"],
    "витамины": ["vitamins", "healthy"],
    "omega-3": ["omega3", "healthy"],
    "антиоксиданты": ["antioxidants", "healthy"],
    "antioxidants": ["antioxidants", "healthy"],
}

# ============================================================================
# COSMETICS DICTIONARIES - Soft recommendations for cosmetics
# ============================================================================

COSMETICS_NEGATIVE = {
    # Irritants (affect Sensitivity, NOT Safety)
    "sodium lauryl sulfate": ["irritant", "harsh_surfactant"],
    "sodium laureth sulfate": ["irritant", "harsh_surfactant"],
    "sls": ["irritant", "harsh_surfactant"],
    "sles": ["irritant", "harsh_surfactant"],
    "fragrance": ["irritant", "fragrance"],
    "parfum": ["irritant", "fragrance"],
    "отдушка": ["irritant", "fragrance"],
    "alcohol": ["irritant", "drying_alcohol"],
    "alcohol denat": ["irritant", "drying_alcohol"],
    "спирт": ["irritant", "drying_alcohol"],
    "phenoxyethanol": ["irritant", "preservative"],
    "sodium chloride": ["irritant", "drying"],
    "соль": ["irritant", "drying"],
    "sulfates": ["irritant", "harsh_surfactant"],
    "сульфаты": ["irritant", "harsh_surfactant"],
}

COSMETICS_POSITIVE = {
    # Positive ingredients for cosmetics
    "glycerin": ["hydrating", "moisturizing"],
    "глицерин": ["hydrating", "moisturizing"],
    "hyaluronic acid": ["hydrating", "moisturizing"],
    "гиалуроновая кислота": ["hydrating", "moisturizing"],
    "ceramides": ["moisturizing", "barrier"],
    "церамиды": ["moisturizing", "barrier"],
    "dimethicone": ["silicone", "anti_frizz"],
    "amodimethicone": ["silicone", "anti_frizz"],
    "silicone": ["silicone", "anti_frizz"],
    "силикон": ["silicone", "anti_frizz"],
    "niacinamide": ["nourishing", "vitamin"],
    "ниацинамид": ["nourishing", "vitamin"],
    "panthenol": ["moisturizing", "soothing"],
    "пантенол": ["moisturizing", "soothing"],
    "squalane": ["moisturizing", "emollient"],
    "сквалан": ["moisturizing", "emollient"],
    "argan oil": ["moisturizing", "hair_care"],
    "масло арганы": ["moisturizing", "hair_care"],
    "coconut oil": ["moisturizing", "hair_care"],
    "кокосовое масло": ["moisturizing", "hair_care"],
}

COSMETICS_HAIR_SPECIFIC = {
    # Hair-specific ingredients
    "curl": ["curl_friendly"],
    "кудрявые": ["curl_friendly"],
    "protein": ["hair_protein"],
    "кератин": ["hair_protein"],
    "keratin": ["hair_protein"],
    "humectant": ["humectant", "hydration"],
    "увлажнитель": ["humectant", "hydration"],
}

# ============================================================================
# HOUSEHOLD DICTIONARIES - Medium strictness for household products
# ============================================================================

HOUSEHOLD_RISK = {
    # High-risk ingredients (only if specified in strict_avoid)
    "bleach": ["toxic", "bleach"],
    "отбеливатель": ["toxic", "bleach"],
    "хлор": ["toxic", "bleach"],
    "chlorine": ["toxic", "bleach"],
    "ammonia": ["toxic", "ammonia"],
    "аммиак": ["toxic", "ammonia"],
    "sodium hypochlorite": ["toxic", "bleach"],
    "гипохлорит натрия": ["toxic", "bleach"],
    "formaldehyde": ["toxic", "formaldehyde"],
    "формальдегид": ["toxic", "formaldehyde"],
    "triclosan": ["toxic", "antibacterial"],
    "триклозан": ["toxic", "antibacterial"],
}

HOUSEHOLD_WARN = {
    # Moderate warnings
    "fragrance": ["irritant", "fragrance"],
    "parfum": ["irritant", "fragrance"],
    "отдушка": ["irritant", "fragrance"],
    "sodium lauryl sulfate": ["irritant", "surfactant"],
    "sodium laureth sulfate": ["irritant", "surfactant"],
    "sls": ["irritant", "surfactant"],
    "sles": ["irritant", "surfactant"],
    "phosphates": ["environmental", "phosphates"],
    "фосфаты": ["environmental", "phosphates"],
    "synthetic dyes": ["irritant", "dyes"],
    "синтетические красители": ["irritant", "dyes"],
}

HOUSEHOLD_POSITIVE = {
    # Positive ingredients for household products
    "plant-based": ["eco_friendly", "natural"],
    "на растительной основе": ["eco_friendly", "natural"],
    "biodegradable": ["eco_friendly", "biodegradable"],
    "биоразлагаемый": ["eco_friendly", "biodegradable"],
    "enzymes": ["natural", "effective"],
    "ферменты": ["natural", "effective"],
    "citric acid": ["natural", "cleaning"],
    "лимонная кислота": ["natural", "cleaning"],
    "vinegar": ["natural", "cleaning"],
    "уксус": ["natural", "cleaning"],
}

