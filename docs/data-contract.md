# Food4U Data Contract

All modules (A, B, C, D) must use the shapes below. To change anything here, agree in the
group chat first, then update this file in the same Pull Request.

Conventions:
- Dates are strings in `YYYY-MM-DD` format.
- Ingredient names are lowercase and must be a key of `INGREDIENTS` (`data/ingredients.py`).
- Recipe `estimated_price` is an estimate. Receipt prices are real. Never mix them.

## 1. INGREDIENTS (`data/ingredients.py`, owner: B)

A dict. Key = ingredient name. Receipt scanning may only map to these keys.

```python
INGREDIENTS = {
    "tomato":  {"display_name": "Tomato",  "aliases": ["tomatoes", "roma tomato"],
                "category": "vegetable", "shelf_days": 7,  "tags": []},
    "chicken": {"display_name": "Chicken", "aliases": ["chicken breast"],
                "category": "meat",      "shelf_days": 3,  "tags": ["meat"]},
    "milk":    {"display_name": "Milk",    "aliases": [],
                "category": "dairy",     "shelf_days": 7,  "tags": ["dairy"]},
    "peanut":  {"display_name": "Peanut",  "aliases": ["peanuts"],
                "category": "nut",       "shelf_days": 180, "tags": ["peanut"]},
}
```

- `display_name`: what the UI shows.
- `aliases`: other names seen on receipts. C uses them to map a receipt line to the key.
- `shelf_days` is only a reference value. Real storage time depends on packaging and storage.

- `shelf_days`: default days until the ingredient should be used, counted from purchase date.
  Used to estimate `expiry_date` because receipts do not contain it.
- `tags`: used to exclude recipes. Allowed tags (extend only by agreement):
  `peanut`, `tree_nut`, `dairy`, `egg`, `gluten`, `soy`, `fish`, `shellfish`,
  `meat`, `pork`, `beef`.

## 2. Preferences (A writes, B reads)

```python
{
    "weekly_budget": 60.0,                 # float, in dollars
    "cuisines": ["chinese", "japanese"],   # list of lowercase strings
    "spice_level": 2,                      # int: 0 none, 1 mild, 2 medium, 3 hot (max the user accepts)
    "flavor": "savory",                    # "sweet" | "savory" | "no_preference"
    "avoid_tags": ["peanut", "dairy"],     # allergies and dietary restrictions, values from the tag list above
}
```

Dietary restrictions map to tags: vegetarian = `meat` (plus `fish`, `shellfish` if wanted),
no pork = `pork`, no beef = `beef`. A's page shows friendly labels, but stores tags.

## 3. Recipe (`data/recipes.json`, owner: B, data entry: A)

```json
{
  "id": 1,
  "name": "Tomato Egg Stir-fry",
  "cuisine": "chinese",
  "spice_level": 0,
  "flavor": "savory",
  "time_minutes": 15,
  "estimated_price": 4.5,
  "ingredients": ["tomato", "egg", "rice"]
}
```

- `ingredients`: names only (no quantities), all must exist in `INGREDIENTS`.
- List ALL ingredients, including sauces and seasonings (soy sauce, oil, ...), because
  their tags also count. A recipe whose ingredient list is incomplete must not be added
  to `recipes.json`, since we cannot promise it is safe for users with allergies.
- A recipe is excluded if any of its ingredients has a tag in the user's `avoid_tags`.

## 4. Pantry item (D provides, B and Pantry page read)

Returned by `get_pantry_items()` as a list of dicts:

```python
{
    "id": 12,
    "ingredient_name": "tomato",
    "quantity": 3.0,
    "unit": "pcs",
    "purchase_date": "2026-11-05",
    "expiry_date": "2026-11-12",   # purchase_date + shelf_days
    "days_left": 5,                # computed by D, can be negative
    "status": "fresh",             # "fresh" | "use_first" | "check_item", computed by D
    "source_receipt_id": 3,        # may be None for manual items
}
```

`status` rules (D implements once, everyone else just reads it):

| status | when | UI wording |
|---|---|---|
| `fresh` | `days_left > 2` | no reminder |
| `use_first` | `1 <= days_left <= 2` | suggest using first |
| `check_item` | `days_left <= 0` | reached its reference date: check it, it can be thrown away |

Dates come from `shelf_days`, which is an estimate, so the wording is a reminder to check,
not a food-safety guarantee. Reminders are computed when the page opens (no background
push needed).

B uses `status == "use_first"` to rank recipes that use soon-to-expire ingredients higher.

## 5. Receipt (C produces, D saves)

Passed to `save_confirmed_receipt(receipt, items)` only after the user clicks Confirm.

```python
receipt = {"store": "Safeway", "purchase_date": "2026-11-05", "total_price": 23.4}

items = [
    {"raw_text": "ROMA TOMATO", "ingredient_name": "tomato", "quantity": 3.0,
     "unit": "pcs", "price": 2.1, "recognized": True},
    {"raw_text": "XYZ SNACK", "ingredient_name": None, "quantity": 1.0,
     "unit": None, "price": 3.0, "recognized": False},   # unrecognized: NOT added to pantry
]
```

- Unrecognized items are saved in `ReceiptItems` but never added to `PantryItems`.
- Deleting a pantry item must NOT delete the receipt record.
- No double saving: after the user clicks Confirm, C disables the button with
  `st.session_state`, and D's `save_confirmed_receipt` must not add the same receipt twice
  (pantry and spending must increase only once).

## 6. Spending summary (D provides, A reads)

`get_spending_summary()` returns:

```python
{"budget": 60.0, "spent": 23.4, "remaining": 36.6}
```

`spent` = sum of `Receipts.total_price` for the current week (Monday to Sunday).

## 7. Functions in `db.py` (owner: D)

```python
get_preferences() -> dict
save_preferences(prefs: dict) -> None
get_pantry_items() -> list[dict]
save_confirmed_receipt(receipt: dict, items: list[dict]) -> None
update_pantry_quantity(item_id: int, quantity: float) -> None   # 0 = used up
get_spending_summary() -> dict
```

A, B, C only call these. They never write SQL.

## 8. Streamlit notes

- Every click re-runs the whole script. Keep temporary UI state in `st.session_state`,
  and anything that must survive a refresh in SQLite (through D's functions).
- Use `st.form` for the preferences page and the receipt confirmation, so changing one
  field does not trigger a save.
- Show receipt results first, write to the database only after the user confirms.
- On Streamlit Cloud the SQLite file is reset on restart. `init_db()` must also insert
  sample data so a demo always works. Do not rely on it to store real user data.
- API keys go in `.streamlit/secrets.toml` locally and in Streamlit Cloud Secrets. Never push them.
