import streamlit as st

from data.ingredients import SPICE_LEVELS
from db import get_pantry_items, get_preferences, get_spending_summary, init_db
from services.recommender import get_recommendations

st.set_page_config(page_title="Food4U · A well-stocked life", page_icon="🥬", layout="wide")

st.markdown("""
<style>
.stApp { background: #f8fae8; color: #17240e; }
[data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"] { display: none; }
[data-testid="stMainBlockContainer"] { max-width: 1500px; padding: 1.5rem 2.5rem 2.5rem; }
h1, h2, h3 { font-family: Georgia, 'Times New Roman', serif !important; color: #17240e; }
h1 { font-size: clamp(2.8rem, 5.2vw, 4.8rem) !important; font-weight: 600 !important; line-height: 1.08 !important; padding-bottom: .4rem !important; }
h3 { font-weight: 500 !important; }
[class*="st-key-nav_"], .st-key-daily_spending, .st-key-weekly_budget {
 background: #edf2d2; border: 0 !important; border-radius: 26px !important;
 padding: 1.4rem !important; position: relative;
}
.st-key-chart_cards [data-testid="stHorizontalBlock"],
.st-key-photo_cards [data-testid="stHorizontalBlock"]:has(.st-key-nav_receipt) {
 display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); align-items: stretch;
}
.st-key-chart_cards [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
.st-key-photo_cards [data-testid="stHorizontalBlock"]:has(.st-key-nav_receipt) > [data-testid="stColumn"] { width: 100%; min-width: 0; }
.st-key-chart_cards [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
.st-key-photo_cards [data-testid="stHorizontalBlock"]:has(.st-key-nav_receipt) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"] { height: 100%; }
.st-key-daily_spending, .st-key-weekly_budget { height: 100%; min-height: 300px; }
.st-key-daily_spending h3, .st-key-weekly_budget h3 { font-size: clamp(1.6rem, 2.6vw, 2.5rem); }
[data-testid="stMetricValue"] { color: #17240e; font-family: Georgia, serif; font-size: 2.8rem; }
.st-key-nav_receipt, .st-key-nav_pantry { height: 100%; min-height: 255px; padding: 1rem !important; }
.st-key-nav_receipt h3, .st-key-nav_pantry h3 { font-size: clamp(1.5rem, 2.4vw, 2.3rem); line-height: 1.05; }
.st-key-photo_cards [data-testid="stImage"] { width: 100%; height: 225px; overflow: hidden; border-radius: 20px; }
.st-key-photo_cards [data-testid="stImage"] img { width: 100%; height: 225px; object-fit: cover; border-radius: 20px; }
.st-key-photo_cards [data-testid="stPageLink"] a { background: #f9fbe8; border-radius: 999px; padding: .4rem .65rem; }
.st-key-nav_settings { padding: 1rem 1.4rem !important; }
.st-key-nav_cuisines, .st-key-nav_spice, .st-key-nav_flavors, .st-key-nav_allergies {
 padding: .85rem 1.4rem !important; gap: .2rem !important;
}
.st-key-nav_cuisines [data-testid="stPageLink"] p,
.st-key-nav_spice [data-testid="stPageLink"] p,
.st-key-nav_flavors [data-testid="stPageLink"] p,
.st-key-nav_allergies [data-testid="stPageLink"] p,
.st-key-nav_settings [data-testid="stPageLink"] p { font-family: Georgia, serif; font-size: 1.4rem; font-weight: 600; }
[data-testid="stPageLink"] a { color: #17240e; font-weight: 600; }
[class*="st-key-nav_"]:not(.st-key-nav_recipes) [data-testid="stPageLink"] a::after {
 content: ""; position: absolute; inset: 0; z-index: 2; border-radius: 26px;
}
[class*="st-key-nav_"] [data-testid="stPageLink"],
[class*="st-key-nav_"] [data-testid="stPageLink"] a,
[class*="st-key-nav_"] [data-testid="stElementContainer"]:has([data-testid="stPageLink"]) { position: static; }
[class*="st-key-nav_"]:not(.st-key-nav_recipes):hover { box-shadow: 0 4px 16px #34432818; }
[class*="st-key-nav_"]:has(a:focus-visible) { outline: 3px solid #526b2e; outline-offset: 3px; }
.st-key-nav_recipes { margin-top: .75rem; padding: 1.7rem !important; }
.st-key-nav_recipes h3 { font-size: 2.6rem; }
.st-key-nav_recipes [data-testid="stImage"] img { max-height: 240px; object-fit: cover; border-radius: 20px; }
.stProgress > div > div > div > div { background-color: #b9d75a; }
@media (max-width: 900px) {
 [data-testid="stMainBlockContainer"] { padding: 1rem; }
 .st-key-nav_receipt [data-testid="stHorizontalBlock"],
 .st-key-nav_pantry [data-testid="stHorizontalBlock"] { flex-direction: column; }
 .st-key-photo_cards [data-testid="stImage"], .st-key-photo_cards [data-testid="stImage"] img { height: 180px; }
}
@media (max-width: 640px) {
 .st-key-chart_cards [data-testid="stHorizontalBlock"],
 .st-key-photo_cards [data-testid="stHorizontalBlock"]:has(.st-key-nav_receipt) { grid-template-columns: minmax(0, 1fr); }
 .st-key-daily_spending, .st-key-weekly_budget { min-height: 0; }
}
</style>
""", unsafe_allow_html=True)


def labels(values):
    if isinstance(values, str):
        values = [v for v in values.split(",") if v]
    return ", ".join(v.replace("_", " ").title() for v in (values or [])) or "None specified"


init_db()
prefs = get_preferences() or {}
summary = get_spending_summary()
pantry = get_pantry_items()

st.caption("🌿 FOOD4U")
st.title("Good food. A little more ease.")
st.write("A thoughtful week starts with what you have, what you love, and room in your budget.")


dashboard_slot = st.container()
recommendation_slot = st.container(border=True, key="nav_recipes")
with recommendation_slot:
    st.caption("FROM YOUR KITCHEN, WITH LOVE")
    st.subheader("This Week’s Recommendation")
    mode_label = st.radio(
        "Find something delicious",
        ["Plan my meals", "Cook with what I have"],
        horizontal=True,
    )
mode = "plan_my_meals" if mode_label == "Plan my meals" else "cook_with_what_i_have"
recommendations = None
try:
    with st.spinner("Finding ideas for your kitchen…"):
        recommendations = get_recommendations(mode)
except (OSError, ValueError, KeyError):
    st.info("Recipe ideas are temporarily unavailable. Your pantry and preferences are still here.")

with dashboard_slot:
    main, utilities = st.columns([3.6, 1], gap="large")
with main:
    spent = summary["spent"]
    if recommendations is not None:
        budget = recommendations["weekly_budget"]
        remaining = recommendations["remaining_budget"]
        default_budget = recommendations["using_default_budget"]
    else:
        budget = prefs.get("weekly_budget")
        default_budget = budget is None or budget == 0
        if default_budget:
            budget = 100.0
        remaining = budget - spent

    with st.container(key="chart_cards"):
        daily, weekly = st.columns(2, gap="medium")
        with daily:
            with st.container(border=True, key="daily_spending"):
                st.subheader("Daily Spending")
                st.metric("Spent this week", f"${spent:,.2f}")
                st.info("Daily spending history is not available yet.")
                st.caption("Monday — Sunday · Daily bars will appear when spending by date is available.")
        with weekly:
            with st.container(border=True, key="weekly_budget"):
                st.subheader("Remaining Budget")
                st.metric("Left this week", f"${remaining:,.2f}")
                st.caption(f"Weekly budget ${budget:,.2f} · Spent ${spent:,.2f}")
                if budget > 0:
                    st.progress(min(max(spent / budget, 0.0), 1.0))
                if default_budget:
                    st.caption("Using the default weekly budget of $100. Set your own in Preferences.")
                if remaining < 0:
                    st.warning("You have exceeded your weekly budget.")
                st.caption("A weekly trend will appear when daily spending history is available.")

    with st.container(key="photo_cards"):
        receipt, fridge = st.columns(2, gap="medium")
        with receipt:
            with st.container(border=True, key="nav_receipt"):
                picture, copy = st.columns([1.05, 1], gap="medium")
                with picture:
                    st.image("https://images.unsplash.com/photo-1542838132-92c53300491e?w=700&auto=format&fit=crop&q=80", width="stretch")
                with copy:
                    st.subheader("Upload Receipt")
                    st.write("Bring your groceries into your kitchen inventory.")
                    st.page_link("pages/3_Receipt.py", label="Upload Receipt →", icon="🧾")
        with fridge:
            with st.container(border=True, key="nav_pantry"):
                picture, copy = st.columns([1.05, 1], gap="medium")
                with picture:
                    st.image("https://images.unsplash.com/photo-1540420773420-3366772f4999?w=700&auto=format&fit=crop&q=80", width="stretch")
                with copy:
                    st.subheader("My Pantry")
                    st.write("See and manage what’s in your kitchen.")
                    count = len({item["ingredient_name"] for item in pantry})
                    st.caption(f"{count} ingredients")
                    st.page_link("pages/4_Pantry.py", label="My Pantry →", icon="🥬")

with utilities:
    with st.container(border=True, key="nav_settings"):
        st.page_link("pages/1_Preferences.py", label="⚙ Preferences →")
    with st.container(border=True, key="nav_cuisines"):
        st.caption("AT YOUR TABLE")
        st.page_link("pages/1_Preferences.py", label="Cuisines →")
        st.write(labels(prefs.get("cuisines")))
    with st.container(border=True, key="nav_spice"):
        st.caption("A LITTLE HEAT")
        st.page_link("pages/1_Preferences.py", label="Spice Level →")
        spice = prefs.get("spice_level")
        if spice is None:
            spice = 0
        st.write(SPICE_LEVELS.get(spice, "Not specified").title())
        if prefs.get("spice_level") is None:
            st.caption("Default: 0 · No spice")
    with st.container(border=True, key="nav_flavors"):
        st.caption("WHAT YOU LOVE")
        st.page_link("pages/1_Preferences.py", label="Flavors →")
        st.write(labels(prefs.get("flavor")))
    with st.container(border=True, key="nav_allergies"):
        st.caption("CHOSEN WITH CARE")
        st.page_link("pages/1_Preferences.py", label="Allergies →")
        st.write(labels(prefs.get("avoid_tags")))

with recommendation_slot:
    results = recommendations.get("results", []) if recommendations is not None else []
    if results:
        result = results[0]
        recipe = result["recipe"]
        photo, details = st.columns([1, 1.7], gap="large")
        with photo:
            st.image("https://images.unsplash.com/photo-1547592180-85f173990554?w=1000&auto=format&fit=crop&q=80", width="stretch")
            st.caption("Kitchen inspiration · illustrative photography")
        with details:
            st.subheader(recipe["name"])
            st.write(f"{labels([recipe['cuisine']])} · {recipe['time_minutes']} min · Estimated ${recipe['estimated_price']:.2f} per serving")
            if result.get("reasons"):
                st.success("Why we picked it: " + "; ".join(result["reasons"]))
            for warning in result.get("warnings", []):
                st.warning(warning)
            missing = result.get("missing_ingredients", [])
            st.write("Shopping list: " + labels(missing) if missing else "Your pantry has all the listed ingredients.")
    else:
        st.info("No recipe suggestions yet. Add pantry items or review your dietary preferences to find your next meal.")
    st.page_link("pages/2_Recipes.py", label="Recipe Recommendation →")

st.caption("Food4U · A well-stocked kitchen. A well-spent week.")
