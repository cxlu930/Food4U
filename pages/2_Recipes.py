import streamlit as st

from data.ingredients import CUISINES, INGREDIENTS
from db import add_favorite, get_favorites, init_db, remove_favorite
from services.recommender import MODE_COOK, MODE_PLAN, get_recommendations

st.set_page_config(page_title="Recipes · Food4U", page_icon="🍽️", layout="wide")

init_db()

CUISINE_EMOJI = {
    "chinese": "🥟",
    "japanese": "🍣",
    "korean": "🍲",
    "indian": "🍛",
    "italian": "🍝",
    "mexican": "🌮",
    "vietnamese": "🍜",
    "western": "🍔",
}

MODES = {
    "Plan My Meals": (
        MODE_PLAN,
        "Plan meals for the week within your budget. Anything missing becomes your shopping list.",
    ),
    "Cook With What I Have": (
        MODE_COOK,
        "Cook now with what is already in your pantry, using up items that expire soon first.",
    ),
}

# Fixed-size emoji tile: always centered and kept inside the card, on desktop and mobile.
st.markdown(
    """
    <style>
    .f4u-emoji {
        width: 88px;
        height: 88px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 52px;
        line-height: 1;
        border-radius: 16px;
        background: rgba(128, 128, 128, 0.08);
        overflow: hidden;
    }

    .stApp:has(.st-key-recipes_page) { background:#FDF9F2; color:#111310; }
    body:has(.st-key-recipes_page) [data-testid="stHeader"],
    body:has(.st-key-recipes_page) [data-testid="stToolbar"],
    body:has(.st-key-recipes_page) [data-testid="stSidebar"] { display:none; }
    body:has(.st-key-recipes_page) [data-testid="stMainBlockContainer"] { max-width:1440px; padding:20px 36px 55px; }
    .st-key-recipes_page { font-family:Arial,Helvetica,sans-serif; }
    .st-key-recipes_page h1, .st-key-recipes_page h2, .st-key-recipes_page h3 { font-family:Arial,Helvetica,sans-serif !important; color:#111310; font-weight:800; }
    .st-key-recipes_page h1 { font-size:clamp(44px,5vw,70px); letter-spacing:-2.5px; }
    .st-key-recipes_page [data-testid="stPageLink"] a { color:#405326; font-weight:700; }
    .st-key-recipes_page [data-testid="stButtonGroup"] > div:last-child { gap:12px; flex-wrap:wrap; }
    .st-key-recipes_page [data-testid="stButtonGroup"] button {
      border-radius:999px !important; background:#FDF9F2; color:#111310;
      border:1px solid #dedbd3; padding:14px 28px; min-height:56px; margin:0 !important;
      font-size:18px; font-weight:600;
    }
    .st-key-recipes_page [data-testid="stButtonGroup"] button p { font-size:18px; font-weight:inherit; }
    /* Streamlit renders this active kind from the recipes_mode widget state. */
    .st-key-recipes_page [data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"],
    .st-key-recipes_page [data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"]:hover {
      background:#D5E69B !important; border-color:#9DBD43 !important; color:#111310; font-weight:800;
    }
    .st-key-recipes_page [data-testid="stButtonGroup"] button:hover { border-color:#9BC336; }
    .st-key-recipes_page [role="radiogroup"] { gap:8px; flex-wrap:wrap; }
    .st-key-recipes_page [role="radiogroup"] label { background:#FDF9F2; border:1px solid #dedbd3; border-radius:999px; padding:7px 13px; margin:0; }
    .st-key-recipes_page [role="radiogroup"] label:has(input:checked) { background:#D2E39A; border-color:#9BC336; }
    .st-key-recipes_page [role="radiogroup"] [data-baseweb="radio"] > div:first-child { display:none; }
    .st-key-recipes_page [class*="st-key-recipe_card_"] { background:#f5f7e9; border:1px solid #d9dfc8 !important; border-radius:22px !important; padding:20px !important; height:100%; }
    .st-key-recipes_page [class*="st-key-recipe_card_"] [data-testid="stMarkdownContainer"] strong { font-weight:800; color:#17240e; }
    .st-key-recipes_page [class*="st-key-recipe_card_"] [data-testid="stCaptionContainer"] { color:#657044; }
    .st-key-recipes_page [class*="st-key-recipe_card_"] [data-testid="stHorizontalBlock"] { align-items:flex-start; }
    .st-key-recipes_page .f4u-emoji { background:#D2E39A; }
    .st-key-recipes_page [class*="st-key-fav_"] button { font-size:26px; padding:0; min-height:0; }
    .st-key-recipes_page [data-testid="stAlertContainer"] { border-radius:14px; }
    .st-key-recipes_page [data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) { background:#fff3c0; color:#9F6634; }
    .st-key-recipes_page [data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) { background:#edf2da; color:#405326; }
    .st-key-recipes_page :is(button,a):focus-visible { outline:2px solid #9BC336; outline-offset:3px; }
    @media(max-width:760px) {
      body:has(.st-key-recipes_page) [data-testid="stMainBlockContainer"] { padding:18px; }
      .st-key-recipes_page [class*="st-key-recipe_card_"] { padding:16px !important; }
      .st-key-recipes_page [data-testid="stButtonGroup"] > div:last-child { width:100%; }
      .st-key-recipes_page [data-testid="stButtonGroup"] button { flex:1 1 100%; padding:13px 20px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def ingredient_label(name):
    return INGREDIENTS.get(name, {}).get("display_name", name.replace("_", " ").title())


def spice_text(level):
    return "🌶️" * level if level else "Not spicy"


def render_card(result, favorites):
    recipe = result["recipe"]
    cuisine = recipe.get("cuisine", "")
    emoji = CUISINE_EMOJI.get(cuisine, "🍽️")

    with st.container(border=True, key=f"recipe_card_{recipe['id']}"):
        left, right = st.columns([1, 3], vertical_alignment="center")
        with left:
            st.markdown(f'<div class="f4u-emoji">{emoji}</div>', unsafe_allow_html=True)
        with right:
            name_col, heart_col = st.columns([6, 1], vertical_alignment="center")
            name_col.markdown(f"**{recipe['name']}**")
            is_favorite = recipe["id"] in favorites
            if heart_col.button(
                "❤️" if is_favorite else "🤍", key=f"fav_{recipe['id']}", type="tertiary",
                help="Remove from favorites" if is_favorite else "Save to favorites",
            ):
                (remove_favorite if is_favorite else add_favorite)(recipe["id"])
                st.rerun()
            st.caption(
                f"{cuisine.replace('_', ' ').title()} · "
                f"${recipe.get('estimated_price', 0):.2f} · "
                f"{recipe.get('time_minutes', '?')} min"
            )
            st.markdown(
                f"{spice_text(recipe.get('spice_level', 0))} · "
                f"Taste: {str(recipe.get('flavor', '')).title()}"
            )

            missing = result["missing_ingredients"]
            if missing:
                st.markdown("**Need to buy:** " + ", ".join(ingredient_label(n) for n in missing))
            else:
                st.markdown("✅ You have everything you need")

            if result.get("reasons"):
                with st.expander("Why this recipe?"):
                    for reason in result["reasons"]:
                        st.text(reason)

            if result["warnings"]:
                st.warning("  \n".join(result["warnings"]), icon="⚠️")


with st.container(key="recipes_page"):
    # ---------- Header and mode switch ----------
    st.page_link("app.py", label="← Back to Home")

    st.title("Recipes")

    mode_label = st.segmented_control(
        "Mode", list(MODES), default="Plan My Meals", label_visibility="collapsed", key="recipes_mode"
    ) or "Plan My Meals"  # clicking the selected option again clears it: fall back to Plan
    mode, description = MODES[mode_label]
    st.caption(description)

    data = get_recommendations(mode)
    favorites = get_favorites()  # recipe ids, most recently saved first

    if data["using_default_budget"]:
        st.info("Using default budget of $100. Set your own in Preferences.")
    if data["using_default_spice"]:
        st.info("Using default spice level: Not spicy. Set your own in Preferences.")

    # ---------- Cuisine filters and recipe cards ----------
    results = data["results"]
    # Favorites only show recipes that fit the user's preferences right now (allergies are never skipped).
    by_id = {result["recipe"]["id"]: result for result in results}
    shown_favorites = [by_id[fid] for fid in favorites if fid in by_id]

    selected_cuisine = st.radio(
        "Cuisine", ["all", "favorites"] + list(CUISINES), horizontal=True,
        format_func=lambda value: (
            "All" if value == "all"
            else f"❤️ Favorites ({len(shown_favorites)})" if value == "favorites"
            else f"{CUISINE_EMOJI[value]} {value.title()}"
        ),
        key="recipes_cuisine",
    )
    if selected_cuisine == "favorites":
        filtered_results = shown_favorites
        category_label = "Favorites"
    else:
        filtered_results = [
            result for result in results
            if selected_cuisine == "all" or result["recipe"]["cuisine"] == selected_cuisine
        ]
        category_label = "All cuisines" if selected_cuisine == "all" else selected_cuisine.title()
    st.subheader(category_label)
    order_text = "Most recently saved first" if selected_cuisine == "favorites" else "Recommended order"
    st.caption(f"{len(filtered_results)} recipe{'s' if len(filtered_results) != 1 else ''} · {order_text}")

    if selected_cuisine == "favorites" and len(favorites) > len(shown_favorites):
        st.info(
            f"{len(favorites) - len(shown_favorites)} saved recipe(s) are hidden because they do not "
            "fit your preferences or this mode right now."
        )

    if not filtered_results and selected_cuisine == "favorites":
        st.info("No favorites to show yet. Tap the heart on a recipe to save it.")
    elif not filtered_results:
        if results:
            st.info(
                f"No {category_label.lower()} recipes match your current settings. "
                "Try All or another cuisine, or update your preferences."
            )
        else:
            st.info(
                "No recipes match right now. Try adjusting your settings in Preferences, "
                "or add ingredients to your Pantry."
            )
        link_left, link_right = st.columns(2)
        link_left.page_link("pages/1_Preferences.py", label="Go to Preferences", icon="⚙️")
        link_right.page_link("pages/4_Pantry.py", label="Go to Pantry", icon="🧺")
    else:
        for start in range(0, len(filtered_results), 2):
            columns = st.columns(2, gap="medium")
            for column, result in zip(columns, filtered_results[start:start + 2]):
                with column:
                    render_card(result, favorites)
