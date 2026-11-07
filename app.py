import streamlit as st

from db import init_db

init_db()

st.title("Food4U (PantryWise)")
st.write("Plan meals, track your pantry, stay on budget.")
