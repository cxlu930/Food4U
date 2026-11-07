import streamlit as st

CUISINES = [
    "chinese",
    "japanese",
    "korean",
    "indian",
    "italian",
    "mexican",
    "vietnamese",
    "north_american"
]

st.title("Food4U")
st.subheader("Your Food Preferences")

with st.form("preferences_form"):
    weekly_budget = st.number_input(
        "Weekly Budget (CAD)",
        min_value=0.0,
        value=60.0,
        step=5.0
    )

    cuisines = st.multiselect(
        "Preferred Cuisines",
        options=CUISINES,
        default=["chinese"],
        format_func=lambda x: x.replace("_", " ").title()
    )

    submitted = st.form_submit_button("Save Preferences")

if submitted:
    preferences = {
        "weekly_budget": weekly_budget,
        "cuisines": cuisines
    }

    st.write(preferences)