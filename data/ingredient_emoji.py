"""One emoji for every ingredient. Used by the Pantry page and by the steps on the Recipes page."""

from data.ingredients import INGREDIENTS

CATEGORY_EMOJI = {
    "vegetable": "🥬", "fruit": "🍎", "meat": "🍗", "seafood": "🐟", "egg": "🥚",
    "protein": "🫘", "dairy": "🧀", "grain": "🌾", "legume": "🫘", "canned": "🥫",
    "condiment": "🧂", "spice": "🌶️", "oil": "🫒", "nut": "🥜", "sweet": "🍫", "sweets": "🍫",
}

INGREDIENT_EMOJI = {
    "tomato": "🍅", "onion": "🧅", "garlic": "🧄", "ginger": "🫚", "green_onion": "🌱", "potato": "🥔",
    "carrot": "🥕", "bell_pepper": "🫑", "broccoli": "🥦", "lettuce": "🥬", "bean_sprouts": "🌱",
    "cilantro": "🌿", "spinach": "🥬", "mushroom": "🍄", "cucumber": "🥒", "napa_cabbage": "🥬",
    "cabbage": "🥬", "bok_choy": "🥬",
    "lemon": "🍋", "lime": "🍋", "banana": "🍌", "avocado": "🥑",
    "chicken": "🍗", "ground_beef": "🥩", "ground_pork": "🥩", "beef": "🥩", "pork_ribs": "🍖", "bacon": "🥓",
    "salmon": "🐟", "shrimp": "🦐", "egg": "🥚", "tofu": "🫘",
    "milk": "🥛", "butter": "🧈", "cheese": "🧀", "parmesan": "🧀", "yogurt": "🥣", "cream": "🥛", "paneer": "🧀",
    "rice": "🍚", "pasta": "🍝", "rice_noodles": "🍜", "bread": "🍞", "burger_bun": "🍔", "flour": "🌾",
    "oats": "🥣", "corn_tortilla": "🌮", "flour_tortilla": "🫓", "naan": "🫓", "rice_paper": "🍘",
    "red_lentils": "🫘", "kidney_beans": "🫘", "canned_tomato": "🥫",
    "soy_sauce": "🍶", "fish_sauce": "🍶", "miso": "🥣", "doubanjiang": "🌶️", "gochujang": "🌶️",
    "kimchi": "🥬", "sesame_oil": "🫙", "sesame_seeds": "🌰", "dashi": "🍲", "curry_roux": "🍛",
    "mayonnaise": "🫙", "ketchup": "🥫", "caesar_dressing": "🥗", "maple_syrup": "🍁",
    "salt": "🧂", "sugar": "🍬", "black_pepper": "🧂", "curry_powder": "🍛", "garam_masala": "🌶️",
    "turmeric": "🧂", "chili_powder": "🌶️", "baking_powder": "🧁", "baking_soda": "🧁",
    "vegetable_oil": "🫙", "olive_oil": "🫒", "peanut": "🥜", "cashew": "🥜",
    "dark_chocolate": "🍫", "chocolate_chips": "🍫", "chocolate_truffles": "🍫", "marshmallow": "🍡",
}


def ingredient_emoji(key):
    """The ingredient's own emoji, else the emoji of its category, else a plate."""
    if key in INGREDIENT_EMOJI:
        return INGREDIENT_EMOJI[key]
    return CATEGORY_EMOJI.get(INGREDIENTS.get(key, {}).get("category"), "🍽️")
