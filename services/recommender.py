# Recipe recommender (owner: B).
#
# Flow:
#   1. Hard filter: drop any recipe whose ingredients carry a tag in the user's avoid_tags.
#      This is a safety rule, never replaced by a score penalty.
#      In "Cook With What I Have", also drop any recipe that uses an expired pantry item,
#      and any recipe missing an ingredient (PANTRY_STAPLES excepted; expired = missing),
#      so Cook mode only shows what can be cooked right now.
#   2. Score the remaining recipes. Both modes use the same function, only the weights differ.
#   3. Return recipe, score, reasons, warnings and missing ingredients, highest score first,
#      plus flags telling the page whether default budget / spice values were used.

import json
from pathlib import Path

from data.ingredients import CUISINES, INGREDIENTS

RECIPES_PATH = Path(__file__).resolve().parent.parent / "data" / "recipes.json"

MODE_PLAN = "plan_my_meals"
MODE_COOK = "cook_with_what_i_have"

# Scoring weights per mode. Tune here.
WEIGHTS = {
    MODE_PLAN: {
        "cuisine_match": 3,       # recipe cuisine is one the user picked
        "coverage": 2,            # x share of ingredients already in the pantry (0..1)
        "use_first": 1,           # per ingredient used that has status "use_first"
        "within_budget": 2,       # estimated_price <= remaining budget
        "over_budget": -3,        # estimated_price > remaining budget
        "spice_over_per_level": -3,  # per level above the user's max spice level
        "flavor_match": 1,        # recipe flavor is one the user likes
    },
    MODE_COOK: {
        "cuisine_match": 2,
        "coverage": 5,
        "use_first": 3,
        "within_budget": 1,
        "over_budget": -1,
        "spice_over_per_level": -3,
        "flavor_match": 1,
    },
}

# Used when the user has not set a weekly budget (None or ""), in CAD. A saved 0 is a real budget.
# Based on a 2026 Interac survey: one person in Canada spends about $102 a week on groceries.
DEFAULT_WEEKLY_BUDGET = 100

# Used when the user has not set the highest spice level they accept: 0 = not spicy.
DEFAULT_SPICE_TOLERANCE = 0

# Basic seasonings and sauces: these are assumed to be always at home; their tags still
# count in the allergen filter. They are not counted in pantry coverage and never listed
# as missing. Fresh items (e.g. green_onion, ginger) do not belong here.
PANTRY_STAPLES = {
    # basics
    "salt", "sugar", "vegetable_oil", "black_pepper",
    # sauces and oils
    "soy_sauce", "sesame_oil", "olive_oil", "fish_sauce", "ketchup", "mayonnaise",
    # dried spices
    "chili_powder", "curry_powder", "turmeric", "garam_masala",
    # baking
    "baking_powder", "baking_soda",
}


def normalize_cuisine(value):
    """Return the CUISINES value for `value`, or None if it is not a known cuisine.

    Lowercases the input, trims it and replaces spaces with underscores,
    so "Chinese" -> "chinese" and " Western " -> "western".
    """
    if not isinstance(value, str):
        return None
    name = "_".join(value.strip().lower().split())
    return name if name in CUISINES else None


def load_recipes(path=RECIPES_PATH):
    """Read the recipe list from data/recipes.json."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _as_list(value):
    """Accept a list or a comma-separated string (older saved preferences)."""
    if value is None:
        return []
    if isinstance(value, str):
        return [v for v in value.split(",") if v.strip()]
    return list(value)


def _display(name):
    return INGREDIENTS[name]["display_name"].lower() if name in INGREDIENTS else name


def is_safe(recipe, avoid_tags):
    """Hard filter. False if any ingredient has an avoided tag, or is unknown
    (an unknown ingredient has no tags we can check, so we cannot promise it is safe)."""
    avoid = set(avoid_tags)
    for name in recipe.get("ingredients", []):
        if name not in INGREDIENTS:
            return False
        if avoid & set(INGREDIENTS[name]["tags"]):
            return False
    return True


def pantry_status(pantry_items):
    """Split the pantry into ingredient-name sets: (available, use_first, expired).

    - available: status "fresh" or "use_first" -> counts as "at home".
    - use_first: about to expire -> bonus points.
    - expired:   status "check_item" and no other usable stock of the same ingredient.
    """
    available, use_first, check = set(), set(), set()
    for item in pantry_items:
        if (item.get("quantity") or 0) <= 0:
            continue
        name, status = item["ingredient_name"], item.get("status")
        if status == "check_item":
            check.add(name)
        else:
            available.add(name)
            if status == "use_first":
                use_first.add(name)
    return available, use_first, check - available


def resolve_settings(prefs, spent=0.0):
    """Fill in defaults for budget and spice tolerance.
    Returns (weekly_budget, remaining_budget, max_spice, using_default_budget, using_default_spice)."""
    budget = prefs.get("weekly_budget")
    # Only a missing value means "not set". 0 is a valid budget: everything with a price
    # is then over budget, and the remaining budget can be 0 or negative.
    using_default_budget = budget is None or budget == ""
    if using_default_budget:
        budget = DEFAULT_WEEKLY_BUDGET
    budget = float(budget)
    remaining = round(budget - (spent or 0), 2)

    max_spice = prefs.get("spice_level")
    using_default_spice = max_spice is None or max_spice == ""
    if using_default_spice:
        max_spice = DEFAULT_SPICE_TOLERANCE
    return budget, remaining, int(max_spice), using_default_budget, using_default_spice


def score_recipe(recipe, prefs, pantry_items, remaining_budget, max_spice, mode=MODE_PLAN):
    """Score one (already filtered) recipe. Returns a result dict:
    {"recipe", "score", "reasons", "warnings", "missing_ingredients"}."""
    w = WEIGHTS[mode]
    score = 0.0
    reasons = []
    warnings = []
    available, use_first, expired = pantry_status(pantry_items)

    # --- cuisine (no bonus for anyone if the user picked none) ---
    wanted = {normalize_cuisine(c) for c in _as_list(prefs.get("cuisines"))} - {None}
    cuisine = normalize_cuisine(recipe.get("cuisine"))
    if wanted and cuisine in wanted:
        score += w["cuisine_match"]
        reasons.append(f"Matches a cuisine you like ({cuisine.replace('_', ' ').title()})")

    # --- pantry coverage (staples excluded; expired items do not count) ---
    needed = [n for n in recipe["ingredients"] if n not in PANTRY_STAPLES]
    have = [n for n in needed if n in available]
    missing = [n for n in needed if n not in available]
    coverage = len(have) / len(needed) if needed else 1.0
    if have:
        score += coverage * w["coverage"]
        reasons.append(f"You already have {len(have)} of {len(needed)} ingredients")

    # --- soon-to-expire ingredients: bonus ---
    for name in recipe["ingredients"]:
        if name in use_first:
            score += w["use_first"]
            reasons.append(f"Uses {_display(name)} which should be used soon")

    # --- expired ingredients (only reached in Plan mode; Cook mode filters them out) ---
    for name in recipe["ingredients"]:
        if name in expired:
            warnings.append(f"Your {_display(name)} has expired, consider buying fresh")

    # --- budget ---
    price = recipe.get("estimated_price")
    if price is not None:
        if price <= remaining_budget:
            score += w["within_budget"]
            reasons.append(
                f"Fits your remaining budget (${price:.2f} of ${remaining_budget:.2f} left)"
            )
        else:
            score += w["over_budget"]
            warnings.append("Over your remaining budget")

    # --- spice: penalty per level above the user's max ---
    over = recipe.get("spice_level", 0) - max_spice
    if over > 0:
        score += over * w["spice_over_per_level"]
        warnings.append("Spicier than you prefer")

    # --- flavor (no bonus for anyone if the user picked none) ---
    liked = set(_as_list(prefs.get("flavor")))
    if liked and recipe.get("flavor") in liked:
        score += w["flavor_match"]
        reasons.append(f"Matches a taste you like ({recipe['flavor']})")

    return {
        "recipe": recipe,
        "score": round(score, 2),
        "reasons": reasons,
        "warnings": warnings,
        "missing_ingredients": missing,
    }


def recommend(recipes, prefs, pantry_items, spent=0.0, mode=MODE_PLAN):
    """Filter, score and sort recipes.

    `spent` is this week's spending (get_spending_summary()["spent"]); the remaining
    budget is computed here so the default budget can be applied.

    Returns:
        {
            "results": [...],               # highest score first; [] if all filtered out
                                            # (Cook mode: only recipes with nothing missing)
            "weekly_budget": 100,
            "remaining_budget": 76.6,
            "max_spice": 0,
            "using_default_budget": True,   # page can say "using default budget $100"
            "using_default_spice": False,   # page can say "assuming you prefer no spice"
        }
    """
    if mode not in WEIGHTS:
        raise ValueError(f"Unknown mode: {mode!r}")

    budget, remaining, max_spice, default_budget, default_spice = resolve_settings(prefs, spent)
    avoid_tags = _as_list(prefs.get("avoid_tags"))
    _, _, expired = pantry_status(pantry_items)

    results = []
    for recipe in recipes:
        if not is_safe(recipe, avoid_tags):
            continue  # safety rule: never shown
        if mode == MODE_COOK and expired & set(recipe["ingredients"]):
            continue  # cooking now with an expired item is not recommended
        result = score_recipe(recipe, prefs, pantry_items, remaining, max_spice, mode)
        if mode == MODE_COOK and result["missing_ingredients"]:
            continue  # Cook mode: only recipes that need nothing new
        results.append(result)
    results.sort(key=lambda r: (-r["score"], r["recipe"].get("id", 0)))

    return {
        "results": results,
        "weekly_budget": budget,
        "remaining_budget": remaining,
        "max_spice": max_spice,
        "using_default_budget": default_budget,
        "using_default_spice": default_spice,
    }


def get_recommendations(mode=MODE_PLAN):
    """Convenience wrapper for the Recipes page: reads everything through db.py."""
    from db import get_pantry_items, get_preferences, get_spending_summary

    return recommend(
        load_recipes(),
        get_preferences(),
        get_pantry_items(),
        get_spending_summary()["spent"],
        mode,
    )
