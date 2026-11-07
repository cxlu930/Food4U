# Food4U (PantryWise)

A web app that helps university students plan meals, track groceries in a pantry, and stay on budget.

Built for HackCamp. Stack: Python, Streamlit, SQLite, requests.

## Core flow

user preferences -> recipe recommendation -> upload receipt photo -> AI extracts items -> user confirms -> pantry updated -> user can edit pantry manually

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Files

- `app.py` - Streamlit entry point (the UI)
- `db.py` - SQLite tables (UserPreferences, Recipes, Receipts, ReceiptItems, PantryItems)

## Team rules

- Deleting a pantry item must NOT delete the receipt record.
- Estimated recipe prices and real receipt prices are stored separately.
- The AI may only map receipt items to our fixed ingredient list; otherwise mark "unrecognized".
