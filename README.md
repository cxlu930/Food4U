# Food4U 🥬

**Less waste. More taste.**

A smarter way to plan meals, manage groceries, and make the most of what's already in your kitchen.

Built for students living independently, Food4U brings personalized recipes, receipt scanning, pantry management, and grocery budgeting together in one place.

**[Try Food4U](https://food4u-3kr5oajjelfqondopan989.streamlit.app/)**

## What it does

- **Personal preferences.** Set your grocery budget, favourite cuisines, spice level, tastes, allergies and dietary needs.
- **Recipe recommendations.** Plan your meals or cook with what you already have. Discover recipes that match your preferences, respect your dietary restrictions, and show what you still need to buy. Every recipe comes with simple step-by-step cooking instructions.
- **Receipt scanning.** Upload a grocery receipt photo. AI reads the items, prices, store and date. You review the results before anything is saved.
- **Fridge scanner.** Snap a photo of your fridge and AI spots the ingredients, so you can see what you can cook right now.
- **Smart pantry.** Confirmed purchases go into your pantry. Update quantities or mark ingredients as used up.
- **Use-first reminders.** Ingredients approaching their reference dates are highlighted and prioritized in recommendations.
- **Budget tracking.** Choose a weekly or monthly budget, track grocery spending, and see how much remains in your Budget Summary.
- **Favorites.** Save recipes you love and find them again anytime.
- **Your own space.** Pick a nickname (no password needed) and your preferences, pantry and favorites stay yours.

## How it works

Set preferences → Discover recipes → Shop & scan receipts → Review & confirm → Update pantry & spending → Cook smarter

## Design principles

- **The AI never invents items.** Receipt items can only be matched to our fixed ingredient list. Unrecognized items are flagged instead of being added to your pantry.
- **You are always in control.** Nothing from a receipt is saved until you confirm it.
- **Safety first for allergies.** Recipes containing ingredients with your selected allergy or dietary tags are excluded.
- **Estimates are labelled.** Recipe prices are estimates, kept separate from actual receipt spending.
- **Reminders, not verdicts.** Reference dates are estimates, not food-safety guarantees. Always check ingredients before cooking.

## Tech stack

Python · Streamlit · SQLite · Google Gemini

## Run it locally

```bash
git clone https://github.com/cxlu930/Food4U.git
cd Food4U
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501).

The database (`food4u.db`) is created automatically on the first run.

Receipt and fridge scanning require a Gemini API key. Create a `.env` file in the project folder:

```env
GEMINI_API_KEY=your-key
```

The rest of the app works without it.

## Project structure

```text
app.py                  Home page
db.py                   Database tables and data functions
pages/                  Preferences, Recipes, Receipt, Pantry, Fridge, Summary
services/               Recommendation, receipt and fridge reading logic
data/                   Ingredient list, recipes and cooking steps
docs/                   Documentation
```

## Built for HackCamp

Team notes (roles, data formats, Git workflow) are in [docs/team-guide.md](docs/team-guide.md).