"""Module C: review and confirm mock receipts without database writes."""

from datetime import date
from hashlib import sha256
from io import BytesIO

from PIL import Image, UnidentifiedImageError
import streamlit as st

from services.receipt_parser import ingredient_catalog, parse_receipt, prepare_confirmation

st.title("Upload Receipt")
st.warning("MOCK DATA — no OCR or AI recognition is performed. The image is not analyzed.")
st.caption("Database integration is pending. Confirmation is temporary and does not save to SQLite.")
uploaded = st.file_uploader("Upload a receipt image", type=["jpg", "jpeg", "png"])
if uploaded is None:
    st.info("Upload a JPG, JPEG or PNG receipt to preview it and review mock results.")
    st.stop()

image_bytes = uploaded.getvalue()
try:
    with Image.open(BytesIO(image_bytes)) as preview:
        if preview.format not in {"JPEG", "PNG"}:
            raise ValueError("Unsupported image format")
        preview.load()
        st.image(preview, caption="Uploaded receipt — mock results below are unrelated to this image")
except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
    st.error("This file cannot be read as a JPG or PNG image. Please upload a valid image.")
    st.stop()

# Content identity prevents duplicate confirmations across reruns and A → B → A uploads.
receipt_id = sha256(image_bytes).hexdigest()
confirmations = st.session_state.setdefault("receipt_c_confirmations", {})
confirmed = receipt_id in confirmations
receipt, items = confirmations[receipt_id] if confirmed else parse_receipt(image_bytes)
catalog = ingredient_catalog()
if not catalog:
    st.info("B's ingredient catalog is not ready. All mock items remain unrecognized until valid keys are available.")

st.subheader("MOCK DATA — review receipt")
st.caption("Checked = recognized; unchecked = unrecognized. Recognition is recalculated from your selected ingredient on confirmation. Unrecognized items will not enter the pantry when database integration is added.")
with st.form(f"receipt_c_form_{receipt_id}"):
    store = st.text_input("Store", value=receipt["store"], disabled=confirmed)
    purchase_date = st.date_input("Purchase date", value=date.fromisoformat(receipt["purchase_date"]), disabled=confirmed)
    total_price = st.number_input("Total price ($)", min_value=0.0, value=receipt["total_price"], step=0.01, disabled=confirmed)
    edited_items = st.data_editor(
        items, key=f"receipt_c_items_{receipt_id}_{confirmed}", hide_index=True,
        num_rows="fixed", disabled=True if confirmed else ["raw_text", "recognized"],
        column_config={
            "raw_text": st.column_config.TextColumn("Original receipt text"),
            "ingredient_name": st.column_config.SelectboxColumn("Ingredient (blank = unknown)", options=sorted(catalog)),
            "quantity": st.column_config.NumberColumn("Quantity", min_value=0.01, step=0.01, required=True),
            "unit": st.column_config.TextColumn("Unit (e.g. pcs, kg, L)"),
            "price": st.column_config.NumberColumn("Price ($)", min_value=0.0, step=0.01, required=True),
            "recognized": st.column_config.CheckboxColumn("Recognized (on confirmation)"),
        },
    )
    submitted = st.form_submit_button("Confirm Receipt", disabled=confirmed)

if submitted and not confirmed:
    try:
        payload = prepare_confirmation(
            {"store": store, "purchase_date": purchase_date.isoformat(), "total_price": total_price},
            edited_items,
        )
    except ValueError as error:
        st.error(str(error))
    else:
        # Integration point for D: save_confirmed_receipt(*payload).
        # Enable once D provides the idempotent API; mark confirmed after success.
        confirmations[receipt_id] = payload
        st.rerun()

if confirmed:
    st.success("MOCK receipt confirmed for this session only. Nothing was permanently saved; database integration is pending.")
