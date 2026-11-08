import streamlit as st

from data.ingredients import INGREDIENTS
from db import init_db
from services.recommender import MODE_COOK, MODE_PLAN, get_recommendations

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
    </style>
    """,
    unsafe_allow_html=True,
)


def ingredient_label(name):
    return INGREDIENTS.get(name, {}).get("display_name", name.replace("_", " ").title())


def spice_text(level):
    return "🌶️" * level if level else "Not spicy"


def render_card(result, mode):
    recipe = result["recipe"]
    cuisine = recipe.get("cuisine", "")
    emoji = CUISINE_EMOJI.get(cuisine, "🍽️")

    with st.container(border=True):
        left, right = st.columns([1, 3], vertical_alignment="center")
        with left:
            st.markdown(f'<div class="f4u-emoji">{emoji}</div>', unsafe_allow_html=True)
        with right:
            st.markdown(f"**{recipe['name']}**")
            st.caption(
                f"{cuisine.replace('_', ' ').title()} · "
                f"${recipe.get('estimated_price', 0):.2f} · "
                f"{recipe.get('time_minutes', '?')} min"
            )
            st.markdown(
                f"{spice_text(recipe.get('spice_level', 0))} · "
                f"Taste: {str(recipe.get('flavor', '')).title()}"
            )

            # Cook mode never shows a shopping list (it only returns recipes with nothing missing).
            missing = result["missing_ingredients"]
            if missing and mode != MODE_COOK:
                st.markdown("**Need to buy:** " + ", ".join(ingredient_label(n) for n in missing))
            elif not missing:
                st.markdown("✅ You have everything you need")

            if result["warnings"]:
                st.warning("  \n".join(result["warnings"]), icon="⚠️")


# ---------- Header and mode switch ----------
st.page_link("app.py", label="← Back to Home")

st.title("Recipes")

mode_label = st.segmented_control(
    "Mode", list(MODES), default="Plan My Meals", label_visibility="collapsed"
) or "Plan My Meals"  # clicking the selected option again clears it: fall back to Plan
mode, description = MODES[mode_label]
st.caption(description)

data = get_recommendations(mode)

# ---------- Budget ----------
budget_col, remaining_col = st.columns(2)
budget_col.metric("Weekly budget", f"${data['weekly_budget']:.2f}")
remaining_col.metric("Remaining this week", f"${data['remaining_budget']:.2f}")

if data["using_default_budget"]:
    st.info("Using default budget of $100. Set your own in Preferences.")
if data["using_default_spice"]:
    st.info("Using default spice level: Not spicy. Set your own in Preferences.")

# ---------- Recipe cards ----------
results = data["results"]
if not results and mode == MODE_COOK:
    st.info(
        "Nothing you can cook with your current pantry. Try Plan My Meals to see "
        "what to buy, or add ingredients in Pantry."
    )
    st.page_link("pages/4_Pantry.py", label="Go to Pantry", icon="🧺")
elif not results:
    st.info(
        "No recipes match right now. Try adjusting your settings in Preferences, "
        "or add ingredients to your Pantry."
    )
    link_left, link_right = st.columns(2)
    link_left.page_link("pages/1_Preferences.py", label="Go to Preferences", icon="⚙️")
    link_right.page_link("pages/4_Pantry.py", label="Go to Pantry", icon="🧺")
else:
    for result in results:
        render_card(result, mode)
