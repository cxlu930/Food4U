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
  `soy`, `wheat`, `dairy`, `egg`, `peanut`, `tree_nut`, `sesame`, `shellfish`,
  `fish`, `meat`, `pork`, `beef` (same as `ALL_TAGS` in `data/ingredients.py`).

## 1b. CUISINES (`data/ingredients.py`, owner: B)

Fixed list. Recipe `cuisine` and preference `cuisines` may only use these values:
`chinese`, `japanese`, `korean`, `indian`, `italian`, `mexican`, `vietnamese`, `western`
(same as `CUISINES` in `data/ingredients.py`).

- Naming rule: all lowercase, multiple words joined with underscores.
- `western` = everyday home cooking from Canada, the US and the UK
  (e.g. mac and cheese, grilled cheese, pancakes, chili, burgers, roast potatoes).
- The preferences page lets the user pick cuisines with a multiselect built from `CUISINES`.
- B compares cuisines with `normalize_cuisine()` in `services/recommender.py`
  (lowercase, spaces to underscores, then check against `CUISINES`).
- Extend only by agreement.

## 1c. UNITS (`data/ingredients.py`, owner: B)

Fixed list. The `unit` field of pantry items (section 4) and receipt items (section 5)
may only use these values:
`pcs`, `g`, `kg`, `lb`, `ml`, `L`, `bag`, `bulb`, `bunch`, `pack`, `can`, `bottle`
(same as `UNITS` in `data/ingredients.py`).

- Naming rule: units are lowercase, except `L` for litres (a lowercase `l` looks like
  the number `1`). Multiple words are joined with underscores.
- Unrecognized receipt items (`ingredient_name` is `None`) have `unit: None`.
  Every recognized item must have a unit from `UNITS`.
- Extend only by agreement.

## 2. Preferences (A writes, B reads)

```python
{
    "weekly_budget": 60.0,                 # float, in dollars (CAD)
    "monthly_budget": 400.0,               # float, saved separately from the weekly one (never weekly x 4)
    "budget_period": "weekly",             # "weekly" or "monthly": which budget the app shows and uses
    "cuisines": ["chinese", "japanese"],   # values from CUISINES, chosen with a multiselect
    "spice_level": 2,                      # int key of SPICE_LEVELS: the highest level the user accepts (single choice)
    "flavor": ["savory", "sour"],          # list of TASTES the user likes (multiple choice), [] = no preference
    "avoid_tags": ["peanut", "dairy"],     # allergies and dietary restrictions, values from the tag list above
}
```

Budget rules:
- Defaults when the user has never saved anything: `weekly_budget` 100.0, `monthly_budget` 400.0
  (its own number, not weekly x 4), `budget_period` "weekly", `spice_level` 0.
- A value the user saved is read as it is. A saved `0` stays `0`; it is never replaced by a default.
- `save_preferences()` keeps any budget field the caller leaves out, so a page that only knows
  `weekly_budget` does not erase the monthly budget or the chosen period.

Dietary restrictions map to tags: vegetarian = `meat` (plus `fish`, `shellfish` if wanted),
no pork = `pork`, no beef = `beef`. A's page shows friendly labels, but stores tags.

Spice level and taste options on the preferences page are read directly from
`SPICE_LEVELS` and `TASTES` in `data/ingredients.py`:

- `SPICE_LEVELS`: `0` none, `1` mild, `2` medium, `3` hot. The user picks the highest
  level they accept (single choice); the page stores the int key.
- `TASTES`: `savory`, `sweet`, `sour`, `mild`. The user picks the tastes they like
  (multiple choice); the page stores a list in `flavor`.

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

- `cuisine`: one value from `CUISINES`.
- `spice_level`: int 0-3, a key of `SPICE_LEVELS`.
- `flavor`: one value from `TASTES`.
- `estimated_price`: estimated cost of ONE serving, in Canadian dollars (CAD).
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

`get_budget_summary(period=None)` is the one place that gives the budget numbers. Leave `period` out to
get the period the user chose (`budget_period`); pass `"weekly"` or `"monthly"` to ask for one.

```python
{
    "period": "monthly",         # "weekly" or "monthly"
    "budget": 450.0,             # that period's budget
    "spent": 23.4,               # total of the receipts the user CONFIRMED in that period
    "remaining": 426.6,          # budget - spent (negative when over budget)
    "start_date": "2026-11-01",  # first day of the period
    "end_date": "2026-11-30",    # last day of the period
    "days_left": 27,             # days left in the period, counting today
    "plan_budget": 106.65,       # what ONE week of meal planning may cost (see below)
}
```

- Weekly = Monday to Sunday. Monthly = the calendar month. Dates follow the **Vancouver** calendar, not
  the server's, so a Sunday evening in Vancouver is still Sunday on Streamlit Cloud.
- `spent` sums `Receipts.total_price` by the receipt's `purchase_date` inside the period. Monthly spending
  is never weekly spending x 4, and a receipt is counted once (a duplicate is refused when saving).
- `plan_budget` is for the recommender: weekly = `remaining`; monthly = `remaining` divided by the
  weeks left in the month (at least 1). Plan My Meals plans one week, so it must not spend the whole
  monthly remainder.

`get_spending_summary()` still exists for older code. It always returns the **weekly** numbers:
`budget`, `spent`, `remaining` are exactly what they were (plus the extra keys above).

## 7. Functions in `db.py` (owner: D)

```python
get_preferences() -> dict
save_preferences(prefs: dict) -> None
get_pantry_items() -> list[dict]
save_confirmed_receipt(receipt: dict, items: list[dict]) -> None
update_pantry_quantity(item_id: int, quantity: float) -> None   # 0 = used up
get_spending_summary() -> dict              # weekly only, kept for older code
get_budget_summary(period: str | None = None) -> dict   # section 6: the chosen period (or "weekly" / "monthly")
add_favorite(recipe_id: int) -> None        # saving twice is fine
remove_favorite(recipe_id: int) -> None     # removing one that is not saved is fine
get_favorites() -> list[int]                # recipe_id of every favorite, most recently saved first
```

`recipe_id` is the `id` of a recipe in `data/recipes.json` (an integer, unique). Favorites store only the
id: to show a favorite, look the recipe up in `recipes.json` by that id. A recipe card knows whether it
is a favorite by checking `recipe["id"] in get_favorites()` (call `get_favorites()` once per page run).

A, B, C only call these. They never write SQL.

**Users.** Every visitor enters a nickname, and all of the data above belongs to that nickname.
Pages do NOT pass a user: each function finds the current visitor itself. If nobody has entered a
nickname yet, the function shows the nickname form and stops the page, so a page never has to
handle "no user". Every function also accepts an optional `user_id=` (used by tests and scripts).
`get_pantry_items()` and the others only ever return the current user's rows.

## 8. Streamlit notes

- Every click re-runs the whole script. Keep temporary UI state in `st.session_state`,
  and anything that must survive a refresh in SQLite (through D's functions).
- Use `st.form` for the preferences page and the receipt confirmation, so changing one
  field does not trigger a save.
- Show receipt results first, write to the database only after the user confirms.
- On Streamlit Cloud the SQLite file is reset on restart. `init_db()` must also insert
  sample data so a demo always works. Do not rely on it to store real user data.
- API keys go in `.streamlit/secrets.toml` locally and in Streamlit Cloud Secrets. Never push them.
