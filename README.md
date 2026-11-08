# Food4U

**Plan smarter. Shop within budget. Waste less food.**

Food4U is a web app for university students who live on their own. It connects meal planning, grocery shopping and your kitchen inventory in one place.

**Live app:** https://food4u-3kr5oajjelfqondopan989.streamlit.app/

## What it does

- **Personal preferences.** Set a weekly budget, favourite cuisines, spice level, tastes, allergies and dietary needs.
- **Recipe recommendations.** Get recipes that match your preferences, never include an ingredient you avoid, and show what you still need to buy.
- **Receipt scanning.** Upload a photo of a grocery receipt. AI reads the items, prices, store and date. You check the result before anything is saved.
- **Smart pantry.** Confirmed purchases go into your pantry. You can change quantities or mark items as used up.
- **Use-first reminders.** Items that are close to their reference date are highlighted, and recipe suggestions favour them, so less food goes to waste.
- **Budget tracking.** See what you spent this week and how much budget is left.

## How it works

preferences -> recipe recommendation -> upload receipt photo -> AI extracts items -> you confirm -> pantry and spending updated -> edit your pantry any time

## Design principles

- **The AI never invents items.** Receipt lines can only be matched to our fixed ingredient list. Anything else is shown as "unrecognized" and is not added to your pantry.
- **You are always in control.** Nothing from a receipt is saved until you confirm it.
- **Safety first for allergies.** A recipe is hidden if any of its ingredients carries an allergy or diet tag you chose.
- **Estimates are labelled.** Recipe prices are estimates and are kept separate from the real prices on your receipts.
- **Reminders, not verdicts.** Reference dates are estimates, not food-safety guarantees. Food4U suggests what to use first and asks you to check items that reached their date.

## Tech stack

Python, Streamlit, SQLite, and Google Gemini for reading receipts.

## Run it locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

The database (`food4u.db`) is created automatically on the first run.

Receipt scanning needs a Gemini API key. Create a file named `.env` in the project folder with one line:

```
GEMINI_API_KEY=your-key
```

The rest of the app works without it.

## Project structure

```
app.py                  Home page
db.py                   Database tables and data functions
pages/                  Preferences, Recipes, Receipt, Pantry
services/               Recommendation and receipt-reading logic
data/                   Ingredient list and recipes
docs/                   Documentation
```

## Built for HackCamp

Team notes (roles, data formats, Git workflow) are in [docs/team-guide.md](docs/team-guide.md).
