# Food4U Team Guide

Internal notes for the four of us. The public overview is in the [README](../README.md).
The shapes of the data passed between modules are in [data-contract.md](data-contract.md). Read that first.

## Who owns what

| | Module | Files |
|---|---|---|
| A | Preferences, budget, home page | `pages/1_Preferences.py` |
| B | Recipes and recommendation | `data/ingredients.py`, `data/recipes.json`, `services/recommender.py`, `pages/2_Recipes.py` |
| C | Receipt scanning | `services/receipt_parser.py`, `pages/3_Receipt.py` |
| D | Database, pantry, integration, deployment | `db.py`, `pages/4_Pantry.py`, `app.py`, `requirements.txt`, `README.md` |

Only edit your own files. If you need a change in someone else's file, ask in the group chat first.

## Database functions

Pages call these functions from `db.py`. They do not write SQL.

| Function | Purpose |
|---|---|
| `get_preferences()` / `save_preferences(prefs)` | Read and save the user's preferences |
| `get_pantry_items()` | Pantry items with `days_left` and `status` (`fresh`, `use_first`, `check_item`) |
| `update_pantry_quantity(item_id, quantity)` | Change a quantity. 0 means used up |
| `save_confirmed_receipt(receipt, items)` | Save a confirmed receipt and add recognized items to the pantry. Returns `False` if the same receipt was already saved |
| `get_budget_summary(period=None)` | Budget, spent, remaining, dates and `plan_budget` for the period the user chose (weekly or monthly). Dates follow the Vancouver calendar |
| `get_spending_summary()` | The **weekly** `budget`, `spent`, `remaining`. Kept for older code; new code should use `get_budget_summary()` |
| `add_favorite(recipe_id)` / `remove_favorite(recipe_id)` | Save or remove a favorite recipe (`recipe_id` is the `id` in `recipes.json`) |
| `get_favorites()` | `recipe_id` of every favorite, most recently saved first |

If you change a table in `db.py`, everyone must delete their local `food4u.db` once (`rm food4u.db`). Say so in the Pull Request.

## Users (nicknames)

Each visitor types a nickname and gets their own preferences, pantry, receipts and budget. There is no password: this separates visitors for the demo, it is not security.

- You do not need to change your page. The `db.py` functions use the current visitor automatically, and show the nickname form if there is none yet.
- The nickname is kept in the web address (`?u=amy`). A normal link that reloads the whole app (`<a href="./Pantry">`) loses it, so write such links as `href="./Pantry{nick_q}"` (see `app.py`). `st.page_link(...)` does not need this.
- To let a page start with the nickname form even before it reads data, call `require_user()` (from `db`) at the top of the page.
- "Switch user" is in the Settings menu on the Home page (it calls `sign_out()` from `db`).
- Old databases upgrade themselves: existing rows go to the nickname `guest`. No need to delete `food4u.db`.
- On Streamlit Cloud the database is reset when the app restarts, so every visitor's data is lost then.

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

## API key (Gemini)

Receipt reading needs `GEMINI_API_KEY`.

- Locally: put it in a file called `.env` in the project folder, on one line: `GEMINI_API_KEY=your-key` (no quotes, no spaces). `.env` is ignored by git.
- Streamlit Cloud: app Settings, then Secrets: `GEMINI_API_KEY = "your-key"`.
- Never put a key in code, in a chat message, or in a Pull Request. If a key leaks, delete it in Google AI Studio and create a new one.

## Deployment

The app runs on Streamlit Community Cloud and redeploys automatically when `main` changes.

- The SQLite file is reset when the app restarts, so do not rely on it to keep real user data.
- `db.py` has a switch `SEED_SAMPLE_DATA`. When it is `True`, an empty pantry is filled with sample items so the demo is never empty.
- Everything the app imports must be listed in `requirements.txt`.
- All visitors share one database (there are no user accounts yet).

## Product rules

- Deleting a pantry item must NOT delete the receipt record.
- Estimated recipe prices and real receipt prices are stored separately.
- The AI may only map receipt items to our fixed ingredient list; otherwise mark "unrecognized". Never invent items.
- The user must confirm receipt results before anything is saved.
- Ingredient `tags` (allergens and diet) are chosen conservatively: a wrongly excluded recipe is better than serving an allergen.
- Expiry reminders: 2 days before the date, suggest using the item first. On or after the date, remind the user to check it (it can be thrown away). Dates are estimates, not food-safety guarantees.
- Units come from `UNITS` in `data/ingredients.py`.
