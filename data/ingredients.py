# Fixed ingredient list. Receipt scanning may only map to keys of INGREDIENTS.
# See docs/data-contract.md section 1.
#
# tags = what the ingredient CONTAINS (allergens / restricted foods), never "who it suits".
# A recipe is excluded if any of its ingredients has a tag in the user's avoid_tags.
# When unsure (brands differ), we tag conservatively: a false exclusion is safer
# than serving an allergen.
#
# shelf_days = reference days from purchase until "use it", assuming normal storage
# (fridge for fresh/perishable items, cupboard for dry goods, unopened for packaged goods).
# It is an estimate, not a food-safety guarantee.

# All allowed tags. A uses this to build the allergy / dietary options.
ALL_TAGS = [
    "soy",
    "wheat",
    "dairy",
    "egg",
    "peanut",
    "tree_nut",
    "sesame",
    "shellfish",
    "fish",
    "meat",   # any meat or poultry (vegetarian users avoid this)
    "pork",
    "beef",
]

# Fixed cuisine list. Recipe "cuisine" and preference "cuisines" may only use these values.
# Rule: all lowercase, multiple words joined with underscores.
# "western" = everyday home cooking from Canada, the US and the UK
# (e.g. mac and cheese, grilled cheese, pancakes, chili, burgers, roast potatoes).
CUISINES = [
    "chinese",
    "japanese",
    "korean",
    "indian",
    "italian",
    "mexican",
    "vietnamese",
    "western",
]

# Spice levels. Recipe "spice_level" must be one of these keys.
# The user picks the highest level they accept (single choice).
SPICE_LEVELS = {
    0: "none",
    1: "mild",
    2: "medium",
    3: "hot",
}

# Tastes. Recipe "flavor" must be one of these values.
# The user picks the tastes they like (multiple choice), stored as a list in preference "flavor".
TASTES = [
    "savory",
    "sweet",
    "sour",
    "mild",
]

# Units for pantry items and receipt items ("unit" field).
# Units are lowercase except "L" for litres (a lowercase "l" looks like the number 1).
# Multiple words would be joined with underscores. Unrecognized receipt items use None.
UNITS = [
    "pcs",     # pieces (tomato, egg, onion)
    "g",       # grams
    "kg",      # kilograms
    "lb",      # pounds, common on Canadian grocery receipts (meat, produce)
    "ml",      # millilitres
    "L",       # litres
    "bag",     # e.g. spinach
    "bulb",    # e.g. garlic
    "bunch",   # e.g. green onion, cilantro
    "pack",    # e.g. tofu, bacon, noodles, tortillas
    "can",     # e.g. canned tomato, kidney beans
    "bottle",  # e.g. soy sauce, oil, ketchup
]


def _item(display_name, category, shelf_days, tags=None, aliases=None):
    """Build one ingredient entry in the data-contract shape."""
    return {
        "display_name": display_name,
        "aliases": aliases or [],
        "category": category,
        "shelf_days": shelf_days,
        "tags": tags or [],
    }


INGREDIENTS = {
    # ---------- Vegetables ----------
    "tomato": _item("Tomato", "vegetable", 7, aliases=["tomatoes", "roma tomato", "tomato on vine"]),
    "onion": _item("Onion", "vegetable", 30, aliases=["onions", "yellow onion", "red onion", "white onion"]),
    "garlic": _item("Garlic", "vegetable", 60, aliases=["garlic bulb", "peeled garlic"]),
    "ginger": _item("Ginger", "vegetable", 21, aliases=["ginger root"]),
    "green_onion": _item("Green Onion", "vegetable", 7, aliases=["green onions", "scallion", "scallions", "spring onion"]),
    "potato": _item("Potato", "vegetable", 30, aliases=["potatoes", "russet potato", "yukon gold", "baby potatoes"]),
    "carrot": _item("Carrot", "vegetable", 21, aliases=["carrots", "baby carrots"]),
    "bell_pepper": _item("Bell Pepper", "vegetable", 7, aliases=["bell peppers", "red pepper", "green pepper", "sweet pepper"]),
    "broccoli": _item("Broccoli", "vegetable", 5, aliases=["broccoli crown", "broccoli florets"]),
    "lettuce": _item("Lettuce", "vegetable", 7, aliases=["romaine", "romaine lettuce", "iceberg lettuce", "romaine hearts"]),
    "bean_sprouts": _item("Bean Sprouts", "vegetable", 3, aliases=["mung bean sprouts", "sprouts"]),
    "cilantro": _item("Cilantro", "vegetable", 5, aliases=["coriander", "fresh coriander"]),
    "spinach": _item("Spinach", "vegetable", 5, aliases=["baby spinach", "spinach bunch"]),
    "mushroom": _item("Mushroom", "vegetable", 7, aliases=["mushrooms", "white mushrooms", "button mushrooms", "cremini", "shiitake"]),
    "cucumber": _item("Cucumber", "vegetable", 7, aliases=["cucumbers", "english cucumber", "mini cucumbers"]),
    "napa_cabbage": _item("Napa Cabbage", "vegetable", 14, aliases=["chinese cabbage", "suey choy", "wombok"]),

    # ---------- Fruit ----------
    "lemon": _item("Lemon", "fruit", 21, aliases=["lemons"]),
    "lime": _item("Lime", "fruit", 21, aliases=["limes"]),
    "banana": _item("Banana", "fruit", 5, aliases=["bananas"]),
    "avocado": _item("Avocado", "fruit", 5, aliases=["avocados", "hass avocado"]),

    # ---------- Meat ----------
    # Meat and seafood are assumed to be stored frozen; 14 days is a reminder window
    # for quality, not a safety limit.
    "chicken": _item("Chicken", "meat", 14, ["meat"],
                     aliases=["chicken breast", "chicken thigh", "chicken thighs", "boneless chicken", "chicken drumsticks"]),
    "ground_beef": _item("Ground Beef", "meat", 14, ["meat", "beef"],
                         aliases=["lean ground beef", "extra lean ground beef", "minced beef", "beef mince"]),
    "ground_pork": _item("Ground Pork", "meat", 14, ["meat", "pork"], aliases=["minced pork", "pork mince"]),
    "bacon": _item("Bacon", "meat", 14, ["meat", "pork"], aliases=["sliced bacon", "side bacon", "bacon strips"]),

    # ---------- Seafood ----------
    "salmon": _item("Salmon", "seafood", 14, ["fish"],
                    aliases=["salmon fillet", "atlantic salmon", "sockeye salmon", "salmon portions"]),
    "shrimp": _item("Shrimp", "seafood", 14, ["shellfish"], aliases=["prawns", "prawn", "frozen shrimp", "raw shrimp"]),

    # ---------- Eggs & tofu ----------
    "egg": _item("Egg", "egg", 28, ["egg"], aliases=["eggs", "large eggs", "free run eggs", "dozen eggs"]),
    "tofu": _item("Tofu", "protein", 5, ["soy"], aliases=["firm tofu", "soft tofu", "silken tofu", "medium tofu"]),

    # ---------- Dairy ----------
    "milk": _item("Milk", "dairy", 7, ["dairy"], aliases=["2% milk", "homo milk", "skim milk", "1% milk", "whole milk"]),
    "butter": _item("Butter", "dairy", 60, ["dairy"], aliases=["salted butter", "unsalted butter"]),
    "cheese": _item("Cheese", "dairy", 30, ["dairy"],
                    aliases=["cheddar", "cheddar cheese", "mozzarella", "shredded cheese", "cheese slices", "marble cheese"]),
    "parmesan": _item("Parmesan", "dairy", 60, ["dairy"], aliases=["parmesan cheese", "grated parmesan", "parmigiano"]),
    "yogurt": _item("Yogurt", "dairy", 14, ["dairy"], aliases=["plain yogurt", "greek yogurt", "yoghurt"]),
    "cream": _item("Cream", "dairy", 7, ["dairy"], aliases=["heavy cream", "whipping cream", "cooking cream", "35% cream"]),
    "paneer": _item("Paneer", "dairy", 7, ["dairy"], aliases=["paneer cheese"]),

    # ---------- Grains, noodles, breads ----------
    "rice": _item("Rice", "grain", 365, aliases=["white rice", "jasmine rice", "basmati rice", "calrose rice", "sushi rice"]),
    "pasta": _item("Pasta", "grain", 365, ["wheat"],
                   aliases=["spaghetti", "penne", "macaroni", "elbow macaroni", "fusilli", "linguine"]),
    "rice_noodles": _item("Rice Noodles", "grain", 365, aliases=["rice vermicelli", "pho noodles", "rice stick"]),
    "bread": _item("Bread", "grain", 5, ["wheat"], aliases=["white bread", "whole wheat bread", "sliced bread", "sourdough"]),
    # Many buns are topped with sesame seeds, so tag sesame to be safe.
    "burger_bun": _item("Burger Bun", "grain", 5, ["wheat", "sesame"], aliases=["hamburger buns", "burger buns", "buns"]),
    "flour": _item("Flour", "grain", 180, ["wheat"], aliases=["all purpose flour", "all-purpose flour", "wheat flour"]),
    "oats": _item("Oats", "grain", 180, aliases=["rolled oats", "quick oats", "oatmeal", "quaker oats"]),
    "corn_tortilla": _item("Corn Tortilla", "grain", 14, aliases=["corn tortillas"]),
    "flour_tortilla": _item("Flour Tortilla", "grain", 14, ["wheat"], aliases=["flour tortillas", "tortilla wraps", "wraps"]),
    # Naan is usually made with yogurt or milk.
    "naan": _item("Naan", "grain", 5, ["wheat", "dairy"], aliases=["naan bread", "garlic naan"]),
    "rice_paper": _item("Rice Paper", "grain", 365, aliases=["rice paper wrappers", "spring roll wrappers"]),

    # ---------- Legumes & canned ----------
    "red_lentils": _item("Red Lentils", "legume", 365, aliases=["lentils", "masoor dal", "split red lentils"]),
    "kidney_beans": _item("Kidney Beans", "legume", 365, aliases=["red kidney beans", "canned kidney beans"]),
    "canned_tomato": _item("Canned Tomato", "canned", 365,
                           aliases=["diced tomatoes", "crushed tomatoes", "tomato sauce", "passata", "tomato paste"]),

    # ---------- Asian sauces & condiments (common hidden allergens) ----------
    "soy_sauce": _item("Soy Sauce", "condiment", 365, ["soy", "wheat"],
                       aliases=["light soy sauce", "dark soy sauce", "shoyu", "kikkoman"]),
    "fish_sauce": _item("Fish Sauce", "condiment", 365, ["fish"], aliases=["nuoc mam"]),
    "miso": _item("Miso", "condiment", 180, ["soy"], aliases=["miso paste", "white miso", "red miso"]),
    # Doubanjiang is made with broad beans and wheat flour; some brands add soybeans.
    "doubanjiang": _item("Doubanjiang", "condiment", 180, ["wheat", "soy"],
                         aliases=["chili bean paste", "broad bean paste", "spicy bean paste"]),
    "gochujang": _item("Gochujang", "condiment", 180, ["wheat", "soy"], aliases=["korean chili paste", "red pepper paste"]),
    # Most kimchi is made with fish sauce and salted shrimp.
    "kimchi": _item("Kimchi", "condiment", 30, ["fish", "shellfish"], aliases=["napa cabbage kimchi", "cabbage kimchi"]),
    "sesame_oil": _item("Sesame Oil", "condiment", 180, ["sesame"], aliases=["toasted sesame oil"]),
    "sesame_seeds": _item("Sesame Seeds", "condiment", 180, ["sesame"], aliases=["toasted sesame seeds"]),
    # Instant dashi is made from bonito (fish).
    "dashi": _item("Dashi", "condiment", 365, ["fish"], aliases=["hondashi", "dashi powder", "bonito stock"]),
    # Japanese curry blocks contain wheat and soy, and many brands contain milk.
    "curry_roux": _item("Japanese Curry Roux", "condiment", 365, ["wheat", "soy", "dairy"],
                        aliases=["curry roux", "golden curry", "vermont curry", "curry blocks"]),

    # ---------- Western sauces & condiments ----------
    "mayonnaise": _item("Mayonnaise", "condiment", 60, ["egg"], aliases=["mayo", "hellmann's"]),
    "ketchup": _item("Ketchup", "condiment", 180, aliases=["tomato ketchup", "heinz ketchup"]),
    # Caesar dressing contains egg, anchovy and parmesan.
    "caesar_dressing": _item("Caesar Dressing", "condiment", 30, ["egg", "fish", "dairy"], aliases=["caesar salad dressing"]),
    "maple_syrup": _item("Maple Syrup", "condiment", 180, aliases=["pure maple syrup", "pancake syrup"]),

    # ---------- Spices & baking ----------
    "salt": _item("Salt", "spice", 1095, aliases=["table salt", "sea salt", "kosher salt"]),
    "sugar": _item("Sugar", "spice", 730, aliases=["white sugar", "granulated sugar", "brown sugar"]),
    "black_pepper": _item("Black Pepper", "spice", 365, aliases=["pepper", "ground black pepper"]),
    "curry_powder": _item("Curry Powder", "spice", 365, aliases=["madras curry powder"]),
    "garam_masala": _item("Garam Masala", "spice", 365, aliases=["garam masala powder"]),
    "turmeric": _item("Turmeric", "spice", 365, aliases=["ground turmeric", "turmeric powder"]),
    "chili_powder": _item("Chili Powder", "spice", 365, aliases=["chilli powder", "chili flakes", "red pepper flakes"]),
    "baking_powder": _item("Baking Powder", "spice", 180, aliases=[]),

    # ---------- Oils ----------
    "vegetable_oil": _item("Vegetable Oil", "oil", 365, aliases=["canola oil", "cooking oil", "sunflower oil"]),
    "olive_oil": _item("Olive Oil", "oil", 365, aliases=["extra virgin olive oil", "evoo"]),

    # ---------- Nuts ----------
    "peanut": _item("Peanut", "nut", 180, ["peanut"], aliases=["peanuts", "roasted peanuts", "peanut butter"]),
    "cashew": _item("Cashew", "nut", 180, ["tree_nut"], aliases=["cashews", "cashew nuts"]),
}
