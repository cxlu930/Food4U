"""Fill a TEMPORARY database with demo receipts for the Budget Summary page.

Creates receipts over the last 4 weeks (dates counted back from date.today()), with items from
many categories plus one unrecognized item, for one nickname. It refuses to touch food4u.db.

Usage (from the project root):
    python scripts/demo_receipts.py --db /tmp/food4u_demo/food4u.db --user demo
    python scripts/demo_receipts.py --db /tmp/food4u_demo/food4u.db --user demo --weekly-budget 0

To look at it in the app, start Streamlit from that folder (db.py opens "food4u.db" in the
current folder, so the real project database is not touched), then open ?u=demo:
    cd /tmp/food4u_demo && python -m streamlit run /workspaces/Food4U/app.py

Running it twice on the same database adds no duplicates (receipts are de-duplicated).
"""
import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import db  # noqa: E402

# (days_ago, store, [(ingredient_name or None, raw_text, price, quantity, unit)])
DEMO_RECEIPTS = [
    (0, "Save-On-Foods", [
        ("chicken", "CHICKEN BREAST", 9.49, 500, "g"), ("rice", "JASMINE RICE 2KG", 6.99, 2, "kg"),
        ("green_onion", "GREEN ONION", 1.29, 1, "bunch"), ("soy_sauce", "SOY SAUCE", 3.49, 1, "bottle"),
    ]),
    (2, "No Frills", [
        ("tomato", "ROMA TOMATO", 2.10, 4, "pcs"), ("egg", "LARGE EGGS 12", 4.79, 12, "pcs"),
        ("milk", "2% MILK 2L", 5.49, 2, "L"), (None, "PAPER TOWEL", 3.99, 1, None),
    ]),
    (6, "T&T Supermarket", [
        ("tofu", "FIRM TOFU", 2.49, 1, "pack"), ("bok_choy", "SHANGHAI BOK CHOY", 2.88, 1, "bunch"),
        ("pork_ribs", "PORK SIDE RIBS", 11.20, 800, "g"), ("dashi", "DASHI STOCK", 4.99, 1, "pack"),
    ]),
    (9, "Safeway", [
        ("pasta", "SPAGHETTI 900G", 2.99, 1, "pack"), ("cheese", "CHEDDAR BLOCK", 7.49, 1, "pack"),
        ("onion", "YELLOW ONION", 1.99, 3, "pcs"), ("banana", "BANANAS", 1.68, 6, "pcs"),
    ]),
    (13, "No Frills", [
        ("ground_beef", "LEAN GROUND BEEF", 8.99, 450, "g"), ("kidney_beans", "RED KIDNEY BEANS", 1.49, 1, "can"),
        ("canned_tomato", "DICED TOMATOES", 1.79, 1, "can"), ("chili_powder", "CHILI POWDER", 2.99, 1, "bottle"),
    ]),
    (17, "Costco", [
        ("salmon", "ATLANTIC SALMON", 16.99, 600, "g"), ("broccoli", "BROCCOLI CROWNS", 3.49, 1, "pcs"),
        ("olive_oil", "OLIVE OIL 1L", 11.99, 1, "bottle"), (None, "DISH SOAP", 4.49, 1, None),
    ]),
    (20, "Safeway", [
        ("yogurt", "GREEK YOGURT", 4.99, 1, "pack"), ("oats", "ROLLED OATS", 3.99, 1, "bag"),
        ("dark_chocolate", "DARK CHOCOLATE", 3.49, 1, "pack"), ("peanut", "ROASTED PEANUTS", 4.29, 1, "pack"),
    ]),
    (25, "T&T Supermarket", [
        ("rice_noodles", "RICE VERMICELLI", 2.49, 1, "pack"), ("shrimp", "FROZEN SHRIMP", 10.99, 1, "bag"),
        ("fish_sauce", "FISH SAUCE", 3.29, 1, "bottle"), ("lime", "LIMES", 1.50, 3, "pcs"),
    ]),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", required=True, help="path of a temporary SQLite file (never food4u.db)")
    parser.add_argument("--user", default="demo", help="nickname to save the receipts for (default: demo)")
    parser.add_argument("--weekly-budget", type=float, default=None,
                        help="also save preferences with this weekly budget (0 is allowed)")
    args = parser.parse_args()

    target = Path(args.db).resolve()
    if target == (ROOT / db.DB_PATH).resolve() or target.parent == ROOT:
        sys.exit("Refusing to write demo data into the real database. Use a temporary path.")

    target.parent.mkdir(parents=True, exist_ok=True)
    db.DB_PATH = str(target)
    db.SEED_SAMPLE_DATA = False
    db.init_db()

    if args.weekly_budget is not None:
        prefs = db.get_preferences(args.user)
        prefs["weekly_budget"] = args.weekly_budget
        db.save_preferences(prefs, args.user)

    added = 0
    for days_ago, store, lines in DEMO_RECEIPTS:
        items = [
            {"ingredient_name": name, "raw_text": raw, "price": price, "quantity": qty,
             "unit": unit, "recognized": name is not None}
            for name, raw, price, qty, unit in lines
        ]
        receipt = {
            "store": store,
            "purchase_date": (date.today() - timedelta(days=days_ago)).isoformat(),
            "total_price": round(sum(item["price"] for item in items), 2),
        }
        added += bool(db.save_confirmed_receipt(receipt, items, args.user))

    print(f"Added {added} demo receipt(s) for '{args.user}' to {target}")


if __name__ == "__main__":
    main()
