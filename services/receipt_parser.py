"""Receipt extraction using Gemini AI and contract validation."""

import os
import streamlit as st
from collections.abc import Mapping
from datetime import date
from math import isfinite

from dotenv import load_dotenv
from google import genai
from google.genai import types

from io import BytesIO
from PIL import Image

from data.ingredients import INGREDIENTS, UNITS

load_dotenv()


def ingredient_catalog():
    """Tolerate B's empty placeholder until the contracted dict is available."""
    return INGREDIENTS if isinstance(INGREDIENTS, Mapping) else {}


def match_ingredient(raw_text):
    """Match catalog keys and aliases; unknown lines stay unrecognized."""
    text = raw_text.strip().casefold()
    for name, details in ingredient_catalog().items():
        if text in [value.strip().casefold() for value in [name, details["display_name"], *details.get("aliases", [])]]:
            return name
    return None


def parse_receipt(image_bytes):
    """Extract receipt information using Gemini AI."""
    import json

    if not image_bytes:
        raise ValueError("Upload a receipt image first.")

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except (KeyError, FileNotFoundError):
            raise ValueError("GEMINI_API_KEY not found.") from None

    client = genai.Client(api_key=api_key)

    with Image.open(BytesIO(image_bytes)) as image:
        image_format = image.format

    if image_format not in ("JPEG", "PNG"):
        raise ValueError("Only JPEG and PNG receipt images are supported.")

    mime_type = "image/jpeg" if image_format == "JPEG" else "image/png"

    catalog = ingredient_catalog()

    ingredient_options = [
        {
            "key": name,
            "display_name": details["display_name"],
            "aliases": details.get("aliases", [])
        }
        for name, details in catalog.items()
    ]

    prompt = f"""
    Extract grocery receipt information from this image.

    Return ONLY a valid JSON object with this structure:
    {{
        "store": "Store name",
        "purchase_date": "YYYY-MM-DD",
        "total_price": 0.0,
        "items": [
            {{
                "raw_text": "Original product name on receipt",
                "ingredient_name": "standard_ingredient_key_or_null",
                "quantity": 1.0,
                "unit": "pcs",
                "price": 0.0
            }}
        ]
    }}

    Rules:
    - Extract only products visible on the receipt.
    - Do not invent products or prices.
    - Allowed units: pcs, g, kg, lb, ml, L, bag, bulb, bunch, pack, can, bottle.
    - Use null for units that cannot be determined.
    - Use null for unknown dates or totals.
    - Return JSON only, without Markdown.

    Ingredient matching rules:
    - Match each receipt product to the most appropriate ingredient from the catalog below.
    - Use the ingredient's standard "key" as ingredient_name.
    - Consider product brands, abbreviations, varieties, and aliases.
    - For example, "WF Large Eggs 18" should match "egg".
    - For example, "W/P Chckn Drumsticks" should match "chicken".
    - Only use keys that exist in the catalog.
    - If there is no appropriate match, return null for ingredient_name.
    - Do not invent new ingredient keys.
    - Always preserve the original product name from the receipt in raw_text.

    Ingredient catalog:
    {json.dumps(ingredient_options)}
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[
            prompt,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0
        )
    )

    data = json.loads(response.text)

    receipt = {
        "store": data.get("store") or "Unknown",
        "purchase_date": data.get("purchase_date") or date.today().isoformat(),
        "total_price": data.get("total_price") or 0.0
    }

    items = []

    for item in data.get("items", []):
        raw_text = item.get("raw_text", "")
        name = item.get("ingredient_name")

        if name not in catalog:
            name = match_ingredient(raw_text)

        unit = item.get("unit")
        if unit not in UNITS:
            unit = None

        items.append({
            "raw_text": raw_text,
            "ingredient_name": name,
            "quantity": item.get("quantity") or 1.0,
            "unit": unit,
            "price": item.get("price") or 0.0,
            "recognized": name is not None
        })

    return receipt, items


def _number(value, label, positive=False):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number.") from None
    if not isfinite(number) or number < 0 or (positive and number == 0):
        raise ValueError(f"{label} must be finite and {'positive' if positive else 'non-negative'}.")
    return number


def prepare_confirmation(receipt, items):
    """Validate edits and return only contract fields for D's future save call."""
    store = receipt["store"].strip()
    if not store:
        raise ValueError("Store name is required.")
    result = {
        "store": store,
        "purchase_date": date.fromisoformat(receipt["purchase_date"]).isoformat(),
        "total_price": _number(receipt["total_price"], "Total price"),
    }
    rows = []
    for index, item in enumerate(items, start=1):
        name = item["ingredient_name"] or None
        if name is not None and name not in ingredient_catalog():
            raise ValueError(f"Item {index}: choose an ingredient from B's catalog.")
        unit = (item["unit"] or "").strip() or None

        if unit is not None and unit not in UNITS:
            raise ValueError(f"Item {index}: select a valid unit.")

        if name and not unit:
            raise ValueError(f"Item {index}: select a unit for the recognized ingredient.")
        rows.append({
            "raw_text": item["raw_text"], "ingredient_name": name,
            "quantity": _number(item["quantity"], f"Item {index} quantity", positive=True),
            "unit": unit, "price": _number(item["price"], f"Item {index} price"),
            "recognized": name is not None,
        })
    return result, rows
