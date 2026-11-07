
import streamlit as st

from db import get_preferences, save_preferences, get_spending_summary
from data.ingredients import ALL_TAGS

CUISINES = [
    "chinese",
    "japanese",
    "korean",
    "indian",
    "italian",
    "mexican",
    "vietnamese",
    "western"
]


FLAVORS = [
    "no_preference",
    "savory",
    "sweet"
]

SPICE_LABELS = ["None", "Mild", "Medium", "Hot"]


def display_name(value):
    return value.replace("_", " ").title()


saved_prefs = get_preferences() or {}

saved_budget = float(saved_prefs.get("weekly_budget", 60.0))
saved_cuisines = [
    cuisine for cuisine in saved_prefs.get("cuisines", ["chinese"])
    if cuisine in CUISINES
]
saved_spice = int(saved_prefs.get("spice_level", 2))
saved_spice = max(0, min(3, saved_spice))

saved_flavor = saved_prefs.get("flavor", "no_preference")
if saved_flavor not in FLAVORS:
    saved_flavor = "no_preference"

saved_tags = [
    tag for tag in saved_prefs.get("avoid_tags", [])
    if tag in ALL_TAGS
]


st.title("Food4U")
st.subheader("Your Food Preferences")


# Preferences form
with st.form("preferences_form"):

    weekly_budget = st.number_input(
        "Weekly Budget (CAD)",
        min_value=0.0,
        value=saved_budget,
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
        options=[0, 1, 2, 3],
        value=saved_spice,
        format_func=lambda x: SPICE_LABELS[x]
    )

    flavor = st.selectbox(
        "Preferred Flavor",
        options=FLAVORS,
        index=FLAVORS.index(saved_flavor),
        format_func=display_name
    )

    avoid_tags = st.multiselect(
        "Allergies and Dietary Restrictions",
        options=ALL_TAGS,
        default=saved_tags,
        format_func=display_name
    )

    submitted = st.form_submit_button(
        "Save Preferences"
    )


if submitted:

    preferences = {
        "weekly_budget": float(weekly_budget),
        "cuisines": cuisines,
        "spice_level": int(spice_level),
        "flavor": flavor,
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
