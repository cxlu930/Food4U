"""Mock extraction and contract validation; no OCR, network or database access."""

from collections.abc import Mapping
from datetime import date
from math import isfinite

from data.ingredients import INGREDIENTS


def ingredient_catalog():
    """Tolerate B's empty placeholder until the contracted dict is available."""
    return INGREDIENTS if isinstance(INGREDIENTS, Mapping) else {}


def match_ingredient(raw_text):
    """Match catalog keys and aliases; unknown lines stay unrecognized."""
    text = raw_text.strip().casefold()
    for name, details in ingredient_catalog().items():
        if text in [value.strip().casefold() for value in [name, *details.get("aliases", [])]]:
            return name
    return None


def parse_receipt(image_bytes):
    """Return fresh MOCK (receipt, items). Image bytes are not analyzed.

    Future OCR replaces extraction here while preserving the return contract.
    """
    if not image_bytes:
        raise ValueError("Upload a receipt image first.")
    receipt = {"store": "Safeway", "purchase_date": "2026-11-05", "total_price": 9.60}
    items = []
    for raw_text, quantity, price in [
        ("ROMA TOMATO", 3.0, 2.10), ("MILK", 1.0, 4.50), ("XYZ SNACK", 1.0, 3.00),
    ]:
        name = match_ingredient(raw_text)
        items.append({
            "raw_text": raw_text, "ingredient_name": name, "quantity": quantity,
            "unit": "pcs" if name else None, "price": price, "recognized": name is not None,
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
        if name and not unit:
            raise ValueError(f"Item {index}: enter a unit for the recognized ingredient.")
        rows.append({
            "raw_text": item["raw_text"], "ingredient_name": name,
            "quantity": _number(item["quantity"], f"Item {index} quantity", positive=True),
            "unit": unit, "price": _number(item["price"], f"Item {index} price"),
            "recognized": name is not None,
        })
    return result, rows
