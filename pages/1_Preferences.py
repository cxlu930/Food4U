import streamlit as st

from db import get_preferences, save_preferences
from data.ingredients import ALL_TAGS, CUISINES, SPICE_LEVELS, TASTES

st.set_page_config(page_title="Preferences · Food4U", page_icon="🌿", layout="wide")

st.markdown("""
<style>
.stApp:has(.st-key-preferences_page) { background: #fdf9f2; color: #111310; }
body:has(.st-key-preferences_page) [data-testid="stHeader"],
body:has(.st-key-preferences_page) [data-testid="stToolbar"],
body:has(.st-key-preferences_page) [data-testid="stSidebar"] { display: none; }
body:has(.st-key-preferences_page) [data-testid="stMainBlockContainer"] {
 max-width: 1440px; padding: 20px 36px 55px;
}
.st-key-preferences_page { font-family: Arial, Helvetica, sans-serif; color: #111310; }
.st-key-preferences_page h1, .st-key-preferences_page h2, .st-key-preferences_page h3 {
 font-family: Arial, Helvetica, sans-serif !important; color: #111310; font-weight: 800;
}
.st-key-preferences_page h1 { font-size: clamp(42px, 4.7vw, 70px); letter-spacing: -2.5px; line-height: 1.05; }
.st-key-preferences_page h3 { font-size: 25px; letter-spacing: -.7px; }
.st-key-preferences_page [data-testid="stPageLink"] a { color: #405326; font-size: 14px; }
.st-key-preferences_page [data-testid="stPageLink"] a:focus-visible { outline: 3px solid #6a8e15; outline-offset: 4px; }
.st-key-preferences_page [data-testid="stForm"] { border: 0; padding: 0; }
.st-key-pref_budget, .st-key-pref_cuisines, .st-key-pref_spice,
.st-key-pref_flavors, .st-key-pref_allergies {
 background: #fdf9f2; border: 1px solid #dedbd3 !important;
 border-radius: 24px !important; padding: 24px !important;
}
.st-key-pref_budget { background: #f0f5cf; margin: 8px 0; }
.st-key-pref_cuisines, .st-key-pref_spice, .st-key-pref_flavors, .st-key-pref_allergies { min-height: 205px; }
.st-key-preferences_page [data-baseweb="input"],
.st-key-preferences_page [data-baseweb="select"] > div {
 background: #fffdf8; border-color: #d8dcc8; border-radius: 12px;
}
.st-key-preferences_page [data-baseweb="input"]:focus-within,
.st-key-preferences_page [data-baseweb="select"]:focus-within > div { border-color: #819e27; box-shadow: 0 0 0 1px #819e27; }
/* Keep inline amount styles inside this budget card only. */
.st-key-pref_budget [data-testid="stNumberInputContainer"],
.st-key-pref_budget [data-testid="stNumberInputContainer"] [data-baseweb="input"],
.st-key-pref_budget [data-testid="stNumberInputContainer"] [data-baseweb="input"] > div {
 background: transparent !important; border: 0 !important; border-radius: 0 !important;
 box-shadow: none !important; outline: none !important;
}
.st-key-pref_budget [data-testid="stNumberInputContainer"] {
 display: flex; align-items: center; gap: 0; min-height: 96px;
}
.st-key-pref_budget [data-testid="stNumberInputContainer"]::before {
 content: "$"; color: #111310; font-family: Arial, Helvetica, sans-serif;
 font-size: clamp(64px, 6vw, 80px); font-weight: 800; line-height: 1.15;
 letter-spacing: -3px; flex-shrink: 0; pointer-events: none;
}
.st-key-pref_budget [data-testid="stNumberInputField"] {
 background: transparent !important; border: 0 !important; outline: none !important;
 box-shadow: none !important; color: #111310 !important;
 font-family: Arial, Helvetica, sans-serif !important;
 font-size: clamp(64px, 6vw, 80px) !important; font-weight: 800 !important;
 line-height: 1.15 !important; letter-spacing: -3px; padding: 0 0 0 3px !important;
 height: 96px; caret-color: #526b2e; appearance: textfield; -moz-appearance: textfield;
}
.st-key-pref_budget [data-testid="stNumberInputField"]::-webkit-inner-spin-button,
.st-key-pref_budget [data-testid="stNumberInputField"]::-webkit-outer-spin-button {
 -webkit-appearance: none; margin: 0;
}
.st-key-pref_budget [data-testid="stNumberInputStepDown"],
.st-key-pref_budget [data-testid="stNumberInputStepUp"],
.st-key-pref_budget [data-testid="InputInstructions"] { display: none !important; }
.st-key-budget_hint { margin-top: -10px; }
.st-key-budget_hint p { color: #89916c; font-size: 12px; margin: 0; }
.st-key-preferences_page [data-baseweb="tag"] { background: #e4edb6; color: #283619; }
.st-key-preferences_page [data-baseweb="tag"] svg { color: #283619; }
.st-key-preferences_page [data-testid="stFormSubmitButton"] button {
 background: #c9e55b; color: #111310; border: 1px solid #b8d44f;
 border-radius: 999px; padding: 10px 28px; font-weight: 700;
}
.st-key-preferences_page [data-testid="stFormSubmitButton"] button:hover { background: #bedb49; color: #111310; border-color: #8fae2f; }
.st-key-preferences_page [data-testid="stFormSubmitButton"] button:focus-visible { outline: 3px solid #6a8e15; outline-offset: 3px; }
@media (max-width: 760px) {
 body:has(.st-key-preferences_page) [data-testid="stMainBlockContainer"] { padding: 18px; }
 .st-key-preferences_page h1 { letter-spacing: -1.5px; }
 .st-key-pref_cuisines, .st-key-pref_spice, .st-key-pref_flavors, .st-key-pref_allergies { min-height: 0; }
}
/* Scope the slider treatment to the Spice Level card. */
.st-key-pref_spice [data-baseweb="slider"] > div > div {
 background: #B8E33D !important; height: 4px !important; border-radius: 999px;
}
.st-key-pref_spice [role="slider"] {
 background: #B8E33D !important; width: 20px !important; height: 20px !important;
 border: 0 !important; border-radius: 50% !important; box-shadow: none !important;
}
.st-key-pref_spice [role="slider"]:focus-visible {
 outline: 2px solid #526b2e; outline-offset: 4px;
}
.st-key-pref_spice [data-testid="stSliderThumbValue"] {
 color: #111310 !important; font-size: 19px !important; font-weight: 750 !important;
 background: transparent !important;
}
.st-key-pref_spice [data-testid="stSliderTickBar"] { color: #687347; }
</style>
""", unsafe_allow_html=True)


def display_name(value):
    return value.replace("_", " ").title()


def saved_options(value, options):
    if isinstance(value, str):
        value = value.split(",")
    if not isinstance(value, list):
        return []
    return [item for item in value if item in options]


saved_prefs = get_preferences()
saved_budget = float(saved_prefs["weekly_budget"])
saved_spice = saved_prefs["spice_level"]
if saved_spice not in SPICE_LEVELS:
    saved_spice = 0

with st.container(key="preferences_page"):
    st.page_link("app.py", label="← Back to Home")
    st.caption("FOOD4U / YOUR PREFERENCES")
    st.title("Make it yours.")
    st.write("Your budget, your favorite flavors, and the things that matter at your table.")

    with st.form("preferences_form", border=False, enter_to_submit=False):
        with st.container(border=True, key="pref_budget"):
            st.subheader("Weekly Budget")
            weekly_budget = st.number_input(
                "Weekly Budget (CAD)", min_value=0.0,
                value=saved_budget, step=0.01, format="%.2f",
                label_visibility="collapsed", key="weekly_budget_inline",
            )

            with st.container(key="budget_hint"):
                st.markdown("Click amount to edit")

        cuisine_col, spice_col = st.columns(2, gap="medium")
        with cuisine_col:
            with st.container(border=True, key="pref_cuisines"):
                st.subheader("Cuisines")
                st.caption("The food you look forward to.")
                cuisines = st.multiselect(
                    "Preferred Cuisines", options=CUISINES,
                    default=saved_options(saved_prefs.get("cuisines"), CUISINES),
                    format_func=display_name,
                )
        with spice_col:
            with st.container(border=True, key="pref_spice"):
                st.subheader("Spice Level")
                st.caption("The highest level of heat you enjoy.")
                spice_level = st.select_slider(
                    "Maximum Spice Level", options=list(SPICE_LEVELS),
                    value=saved_spice,
                    format_func=lambda value: SPICE_LEVELS[value].title(),
                    label_visibility="collapsed",
                )
                st.caption(" → ".join(label.title() for label in SPICE_LEVELS.values()))

        flavor_col, allergy_col = st.columns(2, gap="medium")
        with flavor_col:
            with st.container(border=True, key="pref_flavors"):
                st.subheader("Flavors")
                st.caption("Pick as many as you like, or leave empty for no preference.")
                flavors = st.multiselect(
                    "Preferred Flavors", options=TASTES,
                    default=saved_options(saved_prefs.get("flavor"), TASTES),
                    format_func=display_name,
                )
        with allergy_col:
            with st.container(border=True, key="pref_allergies"):
                st.subheader("Allergies")
                st.caption("Ingredients and dietary tags you want to avoid.")
                avoid_tags = st.multiselect(
                    "Allergies and Dietary Restrictions", options=ALL_TAGS,
                    default=saved_options(saved_prefs.get("avoid_tags"), ALL_TAGS),
                    format_func=display_name,
                )

        submitted = st.form_submit_button("Save Preferences", type="primary")

    if submitted:
        save_preferences({
            "weekly_budget": float(weekly_budget),
            "cuisines": cuisines,
            "spice_level": int(spice_level),
            "flavor": flavors,
            "avoid_tags": avoid_tags,
        })
        st.success("Preferences saved. Your weekly budget is up to date.")
