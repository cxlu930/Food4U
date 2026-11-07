# Food4U

A web app that helps university students plan meals, track groceries in a pantry, and stay on budget.

Plan smarter. Shop within budget. Waste less food.

Built for HackCamp. Stack: Python, Streamlit, SQLite, requests.

**Live app:** https://food4u-3kr5oajjelfqondopan989.streamlit.app/

## Core flow

user preferences -> recipe recommendation -> upload receipt photo -> AI extracts items -> user confirms -> pantry updated -> user can edit pantry manually

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

The database file `food4u.db` is created automatically on first run (it is not committed to git).
If someone changes the table structure in `db.py`, delete your local `food4u.db` once and run again:

```bash
rm food4u.db
```

## Files

```
app.py                     Streamlit entry point
db.py                      SQLite tables and the data functions every page uses
pages/
  1_Preferences.py         Budget, cuisines, spice level, tastes, allergies; spending summary
  2_Recipes.py             Recommended recipes
  3_Receipt.py             Upload a receipt, review the result, confirm
  4_Pantry.py              View and edit pantry items, use-first reminders
services/
  recommender.py           Recipe scoring (no LLM)
  receipt_parser.py        Receipt reading and matching to our ingredient list
data/
  ingredients.py           Fixed ingredient list, tags, shelf days, cuisines, tastes, units
  recipes.json             Recipe data
docs/
  data-contract.md         The shapes of data passed between modules. Read this first.
```

## Who owns what

| | Module | Files |
|---|---|---|
| A | Preferences and budget | `pages/1_Preferences.py` |
| B | Recipes and recommendation | `data/ingredients.py`, `data/recipes.json`, `services/recommender.py`, `pages/2_Recipes.py` |
| C | Receipt scanning | `services/receipt_parser.py`, `pages/3_Receipt.py` |
| D | Database, pantry, integration, deployment | `db.py`, `pages/4_Pantry.py`, `app.py`, `README.md`, `requirements.txt` |

Only edit your own files. If you need a change in someone else's file, ask in the group chat first.

## Database functions

Pages call these functions from `db.py`. They do not write SQL.

| Function | Purpose |
|---|---|
| `get_preferences()` / `save_preferences(prefs)` | Read and save the user's preferences |
| `get_pantry_items()` | Pantry items with `days_left` and `status` (`fresh`, `use_first`, `check_item`) |
| `update_pantry_quantity(item_id, quantity)` | Change a quantity. 0 means used up |
| `save_confirmed_receipt(receipt, items)` | Save a confirmed receipt and add recognized items to the pantry. Returns `False` if the same receipt was already saved |
| `get_spending_summary()` | `budget`, `spent` (this week), `remaining` |

The exact data shapes are in [docs/data-contract.md](docs/data-contract.md).

## Git workflow

Never push directly to `main`. Use a short branch for each task and open a Pull Request.

```bash
git switch main
git pull origin main
git switch -c feature/your-task

# ...work, then only add the files you changed...
git add path/to/your_file.py
git commit -m "Clear message about what changed"
git push -u origin feature/your-task
```

Then open a Pull Request on GitHub, ask a teammate to look at it, and merge. After merging, delete the branch and start the next task from a fresh `main`.

To bring the latest `main` into the branch you are working on, commit or stash your changes first, then:

```bash
git fetch origin
git merge origin/main
```

Before you push, run `streamlit run app.py` and make sure the app starts without errors.

## Deployment

The app runs on Streamlit Community Cloud and redeploys automatically when `main` changes.

- The SQLite file is reset when the app restarts, so do not rely on it to keep real user data.
- `db.py` has a switch `SEED_SAMPLE_DATA`. When it is `True`, an empty pantry is filled with sample items so the demo is never empty.
- Anything the app imports must be in `requirements.txt`.
- API keys go in `.streamlit/secrets.toml` locally and in the Streamlit Cloud Secrets settings. Never commit them.

## Team rules

- Deleting a pantry item must NOT delete the receipt record.
- Estimated recipe prices and real receipt prices are stored separately.
- The AI may only map receipt items to our fixed ingredient list; otherwise mark "unrecognized". Never invent items.
- The user must confirm receipt results before anything is saved.
- Expiry reminders: 2 days before the date, suggest using the item first. On or after the date, remind the user to check it (it can be thrown away). Dates are estimates, not food-safety guarantees.
