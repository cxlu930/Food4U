import streamlit as st

from db import get_preferences, save_preferences, get_spending_summary
from data.ingredients import ALL_TAGS, CUISINES, SPICE_LEVELS, TASTES


def display_name(value):
    return value.replace("_", " ").title()


saved_prefs = get_preferences() or {}

saved_budget = float(saved_prefs.get("weekly_budget") or 100.0)

saved_cuisines = saved_prefs.get("cuisines", [])
if not isinstance(saved_cuisines, list):
    saved_cuisines = []
saved_cuisines = [
    c for c in saved_cuisines if c in CUISINES
]

saved_spice = saved_prefs.get("spice_level", 0)
if saved_spice not in SPICE_LEVELS:
    saved_spice = 0

saved_flavors = saved_prefs.get("flavor", "")
if isinstance(saved_flavors, str):
    saved_flavors = saved_flavors.split(",")
elif not isinstance(saved_flavors, list):
    saved_flavors = []

saved_flavors = [
    f for f in saved_flavors if f in TASTES
]

saved_tags = saved_prefs.get("avoid_tags", [])
if not isinstance(saved_tags, list):
    saved_tags = []
saved_tags = [
    tag for tag in saved_tags if tag in ALL_TAGS
]


st.title("Food4U")
st.subheader("Your Food Preferences")


with st.form("preferences_form"):

    weekly_budget = st.number_input(
        "Weekly Budget (CAD)",
        min_value=0.0,
        value=max(0.0, saved_budget),
        step=5.0
    )

    cuisines = st.multiselect(
        "Preferred Cuisines",
        options=CUISINES,
        default=saved_cuisines,
        format_func=display_name
    )

    spice_level = st.select_slider(
        "Maximum Spice Level",
        options=list(SPICE_LEVELS.keys()),
        value=saved_spice,
        format_func=lambda x: SPICE_LEVELS[x].title()
    )

    flavors = st.multiselect(
        "Preferred Flavors",
        options=TASTES,
        default=saved_flavors,
        format_func=display_name
    )

    avoid_tags = st.multiselect(
        "Allergies and Dietary Restrictions",
        options=ALL_TAGS,
        default=saved_tags,
        format_func=display_name
    )

    submitted = st.form_submit_button("Save Preferences")


if submitted:

    preferences = {
        "weekly_budget": float(weekly_budget),
        "cuisines": cuisines,
        "spice_level": int(spice_level),
        "flavor": flavors,
        "avoid_tags": avoid_tags
    }

    save_preferences(preferences)

    st.success("Preferences saved successfully!")


st.divider()
st.subheader("Weekly Spending Dashboard")

summary = get_spending_summary()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Weekly Budget",
        f"${summary['budget']:.2f}"
    )

with col2:
    st.metric(
        "Spent",
        f"${summary['spent']:.2f}"
    )

with col3:
    st.metric(
        "Remaining",
        f"${summary['remaining']:.2f}"
    )

if summary["remaining"] < 0:
    st.warning("You have exceeded your weekly budget!")
