"""Module C: AI receipt recognition, confirmation, and database integration."""

from datetime import date
from hashlib import sha256
from io import BytesIO

from data.ingredients import UNITS
from db import require_user, save_confirmed_receipt

from PIL import Image, UnidentifiedImageError
import streamlit as st

from services.receipt_parser import ingredient_catalog, parse_receipt, prepare_confirmation

st.set_page_config(page_title="Upload Receipt · Food4U", page_icon="🌿", layout="wide")

require_user()  # know who this is from the first moment, so "Back to Home" keeps the nickname


st.markdown("""
<style>
.stApp:has(.st-key-receipt_page) { background:#FAF8F1; color:#111310; }
body:has(.st-key-receipt_page) [data-testid="stHeader"],
body:has(.st-key-receipt_page) [data-testid="stToolbar"],
body:has(.st-key-receipt_page) [data-testid="stSidebar"] { display:none; }
body:has(.st-key-receipt_page) [data-testid="stMainBlockContainer"] { max-width:1200px; padding:24px 36px 56px; }
.st-key-receipt_page { font-family:Arial,Helvetica,sans-serif; gap:18px; }
.st-key-receipt_page h1 { font-family:inherit !important; font-size:clamp(42px,5vw,68px); font-weight:800; letter-spacing:-2px; line-height:1.1; color:#111310; padding-bottom:0; }
.st-key-receipt_page h3 { font-family:inherit !important; font-size:23px; font-weight:800; letter-spacing:-.5px; color:#111310; }
.st-key-receipt_page [data-testid="stPageLink"] a { color:#526b2e; font-size:14px; }
.st-key-receipt_page .receipt-subtitle { color:#65704f; font-size:18px; margin:0 0 8px; }
.st-key-receipt_upload { background:#EDF3D8; border:1px solid #dbe2c7; border-radius:24px; padding:24px; gap:10px; }
.st-key-receipt_upload [data-testid="stFileUploader"] { padding:0; }
.st-key-receipt_upload [data-testid="stFileUploaderDropzone"] { background:#FAF8F1; border:1.5px dashed #a6b582; border-radius:18px; padding:30px 24px; }
.st-key-receipt_upload [data-testid="stFileUploaderDropzone"] svg { color:#718c3f; }
.st-key-receipt_upload button { background:#C5E95D; color:#17240e; border:1px solid #b8d755; border-radius:999px; font-weight:700; padding:10px 20px; }
.st-key-receipt_page [data-testid="stExpander"] { background:transparent; border:1px solid #e0e1d5; border-radius:16px; }
.st-key-receipt_page [data-testid="stImage"] img { border-radius:12px; max-width:100%; height:auto; }
.st-key-receipt_page [data-testid="stForm"] { background:#EDF3D8; border:1px solid #dbe2c7; border-radius:24px; padding:24px; }
.st-key-receipt_page [data-baseweb="input"], .st-key-receipt_page [data-baseweb="select"] > div { background:#fffdf7; border-color:#d6ddc5; border-radius:10px; }
.st-key-receipt_page [data-baseweb="input"]:focus-within { border-color:#819e27; }
.st-key-receipt_page [data-testid="stDataFrame"] { border-radius:12px; overflow:hidden; border:1px solid #d8dfc6; }
.st-key-receipt_page [data-testid="stFormSubmitButton"] button { background:#C5E95D; color:#111310; border:1px solid #b8d755; border-radius:999px; padding:13px 24px; min-height:48px; font-weight:750; }
.st-key-receipt_page [data-testid="stFormSubmitButton"] button:hover { background:#b8dc4e; border-color:#91ad37; color:#111310; }
.st-key-receipt_page button:focus-visible, .st-key-receipt_page a:focus-visible { outline:3px solid #819e27; outline-offset:3px; }
.st-key-receipt_page button:disabled { opacity:.5; }
.st-key-receipt_page [data-testid="stAlertContainer"] { border-radius:14px; }
.st-key-receipt_page [data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) { background:#fff5d8; border:1px solid #eadfb8; }
.st-key-receipt_page .receipt-status-row { display:flex; flex-wrap:wrap; gap:8px; }
.st-key-receipt_page .receipt-status { font-size:12px; color:#405326; border-radius:999px; padding:7px 12px; background:#e7efce; }
.st-key-receipt_page .receipt-status.needs-attention { background:#fff1c9; color:#826326; }
@media(max-width:760px) {
 body:has(.st-key-receipt_page) [data-testid="stMainBlockContainer"] { padding:18px 16px 36px; }
 .st-key-receipt_upload, .st-key-receipt_page [data-testid="stForm"] { padding:18px; border-radius:20px; }
 .st-key-receipt_upload [data-testid="stFileUploaderDropzone"] { padding:20px 12px; flex-direction:column; align-items:stretch; gap:12px; }
 .st-key-receipt_page [data-testid="stForm"] [data-testid="stHorizontalBlock"] { flex-direction:column; }
 .st-key-receipt_page [data-testid="stForm"] [data-testid="stColumn"] { width:100%; flex:1 1 100%; }
 .st-key-receipt_page h1 { letter-spacing:-1.3px; }
}
</style>
""", unsafe_allow_html=True)

with st.container(key="receipt_page"):
    st.page_link("app.py", label="← Back to Home")

    st.title("Upload Receipt")
    st.markdown('<p class="receipt-subtitle">From your grocery bag to your pantry.</p>', unsafe_allow_html=True)
    with st.container(key="receipt_upload"):
        st.subheader("01 · Upload your receipt")
        st.caption("Choose a clear photo. Scanning starts automatically; you’ll review everything before saving.")
        uploaded = st.file_uploader("Upload a receipt image", type=["jpg", "jpeg", "png"])
    if uploaded is None:
        st.caption("JPG, JPEG or PNG · Keep the store, date and total visible in your photo.")
        st.stop()

    image_bytes = uploaded.getvalue()
    try:
        with Image.open(BytesIO(image_bytes)) as preview:
            if preview.format not in {"JPEG", "PNG"}:
                raise ValueError("Unsupported image format")
            preview.load()
            with st.expander("View uploaded receipt", expanded=True):
                st.image(preview, caption="Uploaded receipt", width=380)
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

    st.subheader("02 · Review your receipt")
    matched_count = sum(item.get("ingredient_name") in catalog for item in items)
    needs_match = len(items) - matched_count
    with st.container(key="receipt_match_summary"):
        st.markdown(
            f'<div class="receipt-status-row"><span class="receipt-status">{matched_count} matched to pantry ingredients</span>'
            f'<span class="receipt-status {"needs-attention" if needs_match else ""}">{needs_match} need an ingredient match</span></div>',
            unsafe_allow_html=True,
        )
    if needs_match and not confirmed:
        st.warning("Some detected items need attention. Choose an ingredient in the table to match them, or leave it blank to keep them out of your pantry.")
    st.caption(
        "Recognition is determined by the selected ingredient. "
        "Recognized items will be added to your Pantry after confirmation. "
        "Unrecognized items will be saved in the receipt history but not added to Pantry."
    )
    with st.form(f"receipt_c_form_{receipt_id}"):
        store_column, date_column, total_column = st.columns([1.4, 1, 1])
        with store_column:
            store = st.text_input("Store", value=receipt["store"], disabled=confirmed)
        with date_column:
            purchase_date = st.date_input("Purchase date", value=date.fromisoformat(receipt["purchase_date"]), disabled=confirmed)
        with total_column:
            total_price = st.number_input("Total price ($)", min_value=0.0, value=receipt["total_price"], step=0.01, disabled=confirmed)
        st.markdown("**Receipt items**")
        st.caption("Edit matches, quantities, units and prices. A blank ingredient means unrecognized; it will not be added to your pantry.")
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
            row_height=44,
            width="stretch",
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
        st.caption("Nothing is saved until you confirm. Only matched ingredients are added to your pantry.")
        submitted = st.form_submit_button("Confirm & Add to Pantry", disabled=confirmed, type="primary", use_container_width=True)

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
