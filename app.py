import streamlit as st

from data.ingredients import SPICE_LEVELS
from db import get_pantry_items, get_preferences, get_spending_summary, init_db
from services.recommender import get_recommendations

st.set_page_config(page_title="Food4U · A well-stocked life", page_icon="🥬", layout="wide")

st.markdown("""
<style>
.stApp { background: #f1f4dc; color: #344328; }
[data-testid="stSidebar"] { display: none; }
[data-testid="stMainBlockContainer"] { max-width: 1500px; padding-top: 2.5rem; }
h1, h2, h3 { font-family: Georgia, 'Times New Roman', serif !important; color: #344328; }
h1 { font-size: clamp(2.5rem, 5vw, 4.6rem) !important; font-weight: 400 !important; }
h3 { font-weight: 400 !important; }
[data-testid="stVerticalBlockBorderWrapper"] > div { border-radius: 24px !important; }
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {
 background: #e3e9ce; border-radius: 24px;
}
[data-testid="stMetricValue"] { color: #344328; font-family: Georgia, serif; }
[data-testid="stImage"] img { border-radius: 18px; object-fit: cover; }
[data-testid="stPageLink"] a { color: #344328; font-weight: 600; }
[class*="st-key-nav_"] { position: relative; }
[class*="st-key-nav_"] [data-testid="stPageLink"] a::after {
 content: ""; position: absolute; inset: 0; z-index: 2; border-radius: 24px;
}
[class*="st-key-nav_"] [data-testid="stPageLink"],
[class*="st-key-nav_"] [data-testid="stPageLink"] a,
[class*="st-key-nav_"] [data-testid="stElementContainer"]:has([data-testid="stPageLink"]) {
 position: static;
}
[class*="st-key-nav_"]:hover { box-shadow: 0 4px 16px #34432818; }
[class*="st-key-nav_"]:has(a:focus-visible) { outline: 3px solid #526b2e; outline-offset: 4px; }
.stProgress > div > div > div > div { background-color: #b9d75a; }
@media (max-width: 700px) {
 [data-testid="stMainBlockContainer"] { padding: 1.5rem 1rem; }
 h1 { font-size: 2.6rem !important; }
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

st.caption("FOOD4U  /  YOUR EVERYDAY KITCHEN")
st.title("Good food. A little more ease.")
st.write("A thoughtful week starts with what you have, what you love, and room in your budget.")
st.write("")

main, utilities = st.columns([4, 1.2], gap="large")
with main:
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

    daily, weekly = st.columns(2, gap="medium")
    with daily:
        with st.container(border=True):
            st.caption("YOUR WEEK IN GROCERIES")
            st.subheader("Daily spending")
            st.metric("Spent this week", f"${spent:,.2f}")
            st.info("Daily spending history is not available yet.")
            st.caption("Monday — Sunday · Daily bars will appear when spending by date is available.")
    with weekly:
        with st.container(border=True):
            st.caption("A LITTLE ROOM TO BREATHE")
            st.subheader("Remaining budget")
            st.metric("Left this week", f"${remaining:,.2f}")
            st.caption(f"Weekly budget ${budget:,.2f} · Spent ${spent:,.2f}")
            if budget > 0:
                st.progress(min(max(spent / budget, 0.0), 1.0))
            if default_budget:
                st.caption("Using the default weekly budget of $100. Set your own in Preferences.")
            if remaining < 0:
                st.warning("You have exceeded your weekly budget.")
            st.caption("A weekly trend will appear when daily spending history is available.")

    receipt, fridge = st.columns(2, gap="medium")
    with receipt:
        with st.container(border=True, key="nav_receipt"):
            st.image("https://images.unsplash.com/photo-1542838132-92c53300491e?w=1000&auto=format&fit=crop&q=80", width="stretch")
            st.subheader("A fresh start, one receipt at a time.")
            st.write("Bring your groceries into your kitchen inventory.")
            st.page_link("pages/3_Receipt.py", label="Upload Receipt →", icon="🧾")
    with fridge:
        with st.container(border=True, key="nav_pantry"):
            st.image("https://images.unsplash.com/photo-1540420773420-3366772f4999?w=1000&auto=format&fit=crop&q=80", width="stretch")
            st.subheader("Good things already in your kitchen.")
            count = len({item["ingredient_name"] for item in pantry})
            st.write(f"{count} distinct ingredients in your pantry.")
            st.page_link("pages/4_Pantry.py", label="My Pantry →", icon="🥬")

    with st.container(border=True, key="nav_recipes"):
        st.caption("FROM YOUR KITCHEN, WITH LOVE")
        st.subheader("This week’s recommendation")
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

with utilities:
    with st.container(border=True, key="nav_settings"):
        st.caption("MAKE IT YOURS")
        st.page_link("pages/1_Preferences.py", label="Preferences", icon="⚙️")
    with st.container(border=True, key="nav_cuisines"):
        st.caption("AT YOUR TABLE")
        st.subheader("Cuisines")
        st.write(labels(prefs.get("cuisines")))
        st.page_link("pages/1_Preferences.py", label="Edit cuisines →")
    with st.container(border=True, key="nav_spice"):
        st.caption("A LITTLE HEAT")
        st.subheader("Spice level")
        spice = prefs.get("spice_level")
        if spice is None:
            spice = 0
        st.write(SPICE_LEVELS.get(spice, "Not specified").title())
        if prefs.get("spice_level") is None:
            st.caption("Default: 0 · No spice")
        st.page_link("pages/1_Preferences.py", label="Edit spice level →")
    with st.container(border=True, key="nav_flavors"):
        st.caption("WHAT YOU LOVE")
        st.subheader("Flavors")
        st.write(labels(prefs.get("flavor")))
        st.page_link("pages/1_Preferences.py", label="Edit flavors →")
    with st.container(border=True, key="nav_allergies"):
        st.caption("CHOSEN WITH CARE")
        st.subheader("Dietary needs")
        st.write(labels(prefs.get("avoid_tags")))
        st.page_link("pages/1_Preferences.py", label="Edit dietary needs →")

st.caption("Food4U · A well-stocked kitchen. A well-spent week.")
