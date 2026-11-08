"""Module C: AI receipt recognition, confirmation, and database integration."""

from datetime import date
from hashlib import sha256
from io import BytesIO

from data.ingredients import UNITS
from db import require_user, save_confirmed_receipt

from PIL import Image, UnidentifiedImageError
import streamlit as st

from services.receipt_parser import ingredient_catalog, parse_receipt, prepare_confirmation

require_user()  # know who this is from the first moment, so "Back to Home" keeps the nickname

st.page_link("app.py", label="← Back to Home")

st.title("Upload Receipt")
st.info("Upload a grocery receipt to extract items using Gemini AI.")
st.caption("Review and edit the extracted information before saving to your Pantry.")
uploaded = st.file_uploader("Upload a receipt image", type=["jpg", "jpeg", "png"])
if uploaded is None:
    st.info("Upload a JPG, JPEG or PNG receipt to start AI recognition.")
    st.stop()

image_bytes = uploaded.getvalue()
try:
    with Image.open(BytesIO(image_bytes)) as preview:
        if preview.format not in {"JPEG", "PNG"}:
            raise ValueError("Unsupported image format")
        preview.load()
        st.image(preview, caption="Uploaded receipt")
except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
    st.error("This file cannot be read as a JPG or PNG image. Please upload a valid image.")
    st.stop()

# Content identity prevents duplicate confirmations across reruns and A → B → A uploads.
receipt_id = sha256(image_bytes).hexdigest()
confirmations = st.session_state.setdefault("receipt_c_confirmations", {})
confirmed = receipt_id in confirmations
if confirmed:
    receipt, items = confirmations[receipt_id]
else:
    extraction_cache = st.session_state.setdefault("receipt_c_extractions", {})

    if receipt_id not in extraction_cache:
        try:
            with st.spinner("Analyzing receipt with Gemini AI..."):
                extraction_cache[receipt_id] = parse_receipt(image_bytes)
        except Exception as error:
            st.error(f"Receipt recognition failed: {error}")
            st.stop()

    receipt, items = extraction_cache[receipt_id]
catalog = ingredient_catalog()
if not catalog:
    st.info("The ingredient catalog is not ready. Items may remain unrecognized until valid ingredients are available.")

st.subheader("Review AI-Extracted Receipt")
st.caption(
    "Recognition is determined by the selected ingredient. "
    "Recognized items will be added to your Pantry after confirmation. "
    "Unrecognized items will be saved in the receipt history but not added to Pantry."
)
with st.form(f"receipt_c_form_{receipt_id}"):
    store = st.text_input("Store", value=receipt["store"], disabled=confirmed)
    purchase_date = st.date_input("Purchase date", value=date.fromisoformat(receipt["purchase_date"]), disabled=confirmed)
    total_price = st.number_input("Total price ($)", min_value=0.0, value=receipt["total_price"], step=0.01, disabled=confirmed)
    edited_items = st.data_editor(
        items,
        column_order=[
            "raw_text",
            "ingredient_name",
            "quantity",
            "unit",
            "price",
        ],
        key=f"receipt_c_items_{receipt_id}_{confirmed}",
        hide_index=True,
        num_rows="fixed", disabled=True if confirmed else ["raw_text", "recognized"],
        column_config={
            "raw_text": st.column_config.TextColumn("Original receipt text"),
            "ingredient_name": st.column_config.SelectboxColumn("Ingredient (blank = unknown)", options=sorted(catalog)),
            "quantity": st.column_config.NumberColumn("Quantity", min_value=0.01, step=0.01, required=True),
            "unit": st.column_config.SelectboxColumn(
                "Unit",
                options=list(UNITS),
                required=False
            ),
            "price": st.column_config.NumberColumn("Price ($)", min_value=0.0, step=0.01, required=True),
        },
    )
    submitted = st.form_submit_button("Confirm Receipt", disabled=confirmed)

if submitted and not confirmed:
    try:
        receipt_data, items_data = prepare_confirmation(
            {
                "store": store,
                "purchase_date": purchase_date.isoformat(),
                "total_price": total_price,
            },
            edited_items,
        )

        saved = save_confirmed_receipt(receipt_data, items_data)

    except Exception as error:
        st.error(f"Failed to save receipt: {error}")

    else:
        confirmations[receipt_id] = (receipt_data, items_data)

        if saved:
            st.session_state[f"receipt_c_saved_{receipt_id}"] = True
        else:
            st.session_state[f"receipt_c_saved_{receipt_id}"] = False

        st.rerun()

if confirmed:
    if st.session_state.get(f"receipt_c_saved_{receipt_id}", False):
        st.success(
            "Receipt saved successfully! Pantry inventory and spending have been updated."
        )
    else:
        st.warning(
            "This receipt was already saved. No duplicate items were added."
        )