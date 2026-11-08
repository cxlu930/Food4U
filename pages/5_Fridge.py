
"""Fridge Scanner: detect ingredients and recommend recipes."""

from io import BytesIO

import streamlit as st
from PIL import Image, UnidentifiedImageError

from data.ingredients import INGREDIENTS
from db import require_user
from services.fridge_parser import scan_fridge
from services.recommender import (
    MODE_COOK,
    load_recipes,
    recommend,
)

require_user()  # know who this is from the first moment, so "Back to Home" keeps the nickname

st.page_link("app.py", label="← Back to Home")

st.title("Fridge Scanner")
st.write(
    "Upload a photo of your fridge and discover "
    "recipes you can make with the ingredients inside."
)

uploaded = st.file_uploader(
    "Upload a fridge photo",
    type=["jpg", "jpeg", "png"],
)

if uploaded is None:
    st.info("Upload a fridge photo to get recipe recommendations.")
    st.stop()

image_bytes = uploaded.getvalue()

try:
    with Image.open(BytesIO(image_bytes)) as image:
        if image.format not in ("JPEG", "PNG"):
            raise ValueError("Unsupported image format.")

        image.load()
        mime_type = (
            "image/jpeg" if image.format == "JPEG"
            else "image/png"
        )

        st.image(image, caption="Your fridge photo")

except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
    st.error("Please upload a valid JPG or PNG image.")
    st.stop()


# Remember results for this upload, avoiding repeated API calls.
import hashlib

photo_id = hashlib.sha256(image_bytes).hexdigest()
cache = st.session_state.setdefault("fridge_scan_cache", {})

if photo_id not in cache:
    try:
        with st.spinner("Scanning your fridge with Gemini AI..."):
            cache[photo_id] = scan_fridge(image_bytes, mime_type)
    except Exception as error:
        st.error(f"Fridge scanning failed: {error}")
        st.stop()

detected = cache[photo_id]

st.subheader("Detected Ingredients")

if not detected:
    st.warning("No recognizable ingredients were found.")
    st.stop()

st.write(
    ", ".join(
        INGREDIENTS[name]["display_name"]
        for name in detected
    )
)


# Convert detected ingredients into temporary recommender input.
temporary_pantry = [
    {
        "ingredient_name": name,
        "quantity": 1,
        "status": "fresh",
    }
    for name in detected
]


# Use B's existing recipe recommendation algorithm.
try:
    recommendations = recommend(
        recipes=load_recipes(),
        prefs={},
        pantry_items=temporary_pantry,
        spent=0.0,
        mode=MODE_COOK,
    )
except Exception as error:
    st.error(f"Recipe recommendation failed: {error}")
    st.stop()


st.subheader("Recommended Recipes")

results = recommendations["results"]

if not results:
    st.info(
        "No recipes can be made using only the detected ingredients. "
        "Try another fridge photo with more visible ingredients."
    )
else:
    st.success(f"Found {len(results)} recipes!")

    for result in results:
        recipe = result["recipe"]

        with st.expander(recipe.get("name", "Recipe")):
            st.write(
                "Cuisine:",
                recipe.get("cuisine", "Unknown")
            )

            st.write(
                "Ingredients:",
                ", ".join(
                    INGREDIENTS[name]["display_name"]
                    for name in recipe["ingredients"]
                    if name in INGREDIENTS
                )
            )

            if recipe.get("estimated_price") is not None:
                st.write(
                    "Estimated price:",
                    f"${recipe['estimated_price']:.2f}"
                )

            st.write(
                "Spice level:",
                recipe.get("spice_level", 0)
            )
