import sqlite3
from datetime import date, timedelta

from data.ingredients import INGREDIENTS

DB_PATH = "food4u.db"

# Demo only: fill an empty pantry with sample items. Set to False to turn it off.
SEED_SAMPLE_DATA = True


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    conn.executescript(
        """
        -- Only one row (id = 1): there are no user accounts yet.
        CREATE TABLE IF NOT EXISTS UserPreferences (
            id INTEGER PRIMARY KEY,
            weekly_budget REAL,
            cuisines TEXT,               -- comma-separated, e.g. "chinese,japanese"
            spice_level INTEGER,         -- 0 none, 1 mild, 2 medium, 3 hot
            flavor TEXT,                 -- comma-separated TASTES, e.g. "savory,sour"; empty = no preference
            avoid_tags TEXT              -- comma-separated allergy / diet tags
        );

        CREATE TABLE IF NOT EXISTS Recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cuisine TEXT,
            ingredients TEXT,            -- comma-separated ingredient names
            estimated_price REAL         -- estimate only, NOT a real receipt price
        );

        CREATE TABLE IF NOT EXISTS Receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store TEXT,
            purchase_date TEXT,
            total_price REAL             -- real price from the receipt
        );

        CREATE TABLE IF NOT EXISTS ReceiptItems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id INTEGER NOT NULL REFERENCES Receipts(id),
            ingredient_name TEXT,        -- NULL if unrecognized
            raw_text TEXT,
            price REAL,
            recognized INTEGER DEFAULT 1 -- 0 = unrecognized
        );

        -- No foreign key to Receipts on purpose:
        -- deleting a pantry item must NOT delete the receipt record.
        CREATE TABLE IF NOT EXISTS PantryItems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_name TEXT NOT NULL,
            quantity REAL,
            unit TEXT,
            purchase_date TEXT,          -- YYYY-MM-DD
            expiry_date TEXT,            -- purchase_date + shelf_days (an estimate)
            source_receipt_id INTEGER
        );
        """
    )
    if SEED_SAMPLE_DATA:
        _seed_sample_data(conn)
    conn.commit()
    conn.close()


def _seed_sample_data(conn):
    # Only seed an EMPTY pantry, so restarting the app never inserts duplicates.
    if conn.execute("SELECT COUNT(*) FROM PantryItems").fetchone()[0] > 0:
        return

    # (ingredient_name, quantity, unit, days_ago_bought, days_left)
    # Dates are relative to today, so every status always shows up in a demo.
    samples = [
        ("tomato", 4, "pcs", 2, 5),        # fresh
        ("rice", 2, "kg", 10, 300),        # fresh
        ("onion", 3, "pcs", 3, 27),        # fresh
        ("garlic", 1, "bulb", 5, 40),      # fresh
        ("carrot", 5, "pcs", 4, 15),       # fresh
        ("chicken", 500, "g", 6, 1),       # use_first
        ("egg", 6, "pcs", 10, 2),          # use_first
        ("spinach", 1, "bag", 5, 0),       # check_item (reached its date today)
        ("milk", 1, "L", 9, -2),           # check_item (past its date)
    ]
    today = date.today()
    rows = [
        (
            name,
            quantity,
            unit,
            (today - timedelta(days=days_ago)).isoformat(),
            (today + timedelta(days=days_left)).isoformat(),
        )
        for name, quantity, unit, days_ago, days_left in samples
    ]
    conn.executemany(
        "INSERT INTO PantryItems (ingredient_name, quantity, unit, purchase_date, "
        "expiry_date) VALUES (?, ?, ?, ?, ?)",
        rows,
    )


# ---------------------------------------------------------------------------
# Data functions for A, B, C. Shapes follow docs/data-contract.md.
# Functions marked TODO are still placeholders; the rest use real SQL.
# ---------------------------------------------------------------------------


def get_preferences():
    conn = get_connection()
    row = conn.execute(
        "SELECT weekly_budget, cuisines, spice_level, flavor, avoid_tags "
        "FROM UserPreferences WHERE id = 1"
    ).fetchone()
    conn.close()

    if row is None:  # nothing saved yet: return empty defaults
        return {
            "weekly_budget": 0.0,
            "cuisines": [],
            "spice_level": 0,
            "flavor": [],
            "avoid_tags": [],
        }

    weekly_budget, cuisines, spice_level, flavor, avoid_tags = row
    return {
        "weekly_budget": weekly_budget,
        # "a,b" -> ["a", "b"]; empty string -> []
        "cuisines": [c for c in (cuisines or "").split(",") if c],
        "spice_level": spice_level,
        "flavor": [f for f in (flavor or "").split(",") if f and f != "no_preference"],
        "avoid_tags": [t for t in (avoid_tags or "").split(",") if t],
    }


def save_preferences(prefs):
    flavor = prefs["flavor"]
    if isinstance(flavor, str):  # accept "savory,sour" too, in case a page still sends text
        flavor = flavor.split(",")

    conn = get_connection()
    # INSERT OR REPLACE with id = 1 overwrites the single preferences row.
    conn.execute(
        "INSERT OR REPLACE INTO UserPreferences "
        "(id, weekly_budget, cuisines, spice_level, flavor, avoid_tags) "
        "VALUES (1, ?, ?, ?, ?, ?)",
        (
            prefs["weekly_budget"],
            ",".join(prefs["cuisines"]),  # ["a", "b"] -> "a,b"
            prefs["spice_level"],
            ",".join(f for f in flavor if f and f != "no_preference"),
            ",".join(prefs["avoid_tags"]),
        ),
    )
    conn.commit()
    conn.close()


def get_pantry_items():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, ingredient_name, quantity, unit, purchase_date, expiry_date, "
        "source_receipt_id FROM PantryItems "
        "WHERE quantity > 0 "  # quantity 0 = used up, hide it
        "ORDER BY expiry_date IS NULL, expiry_date"  # soonest first, no date last
    ).fetchall()
    conn.close()

    items = []
    for id_, name, quantity, unit, purchase_date, expiry_date, receipt_id in rows:
        if expiry_date:
            days_left = (date.fromisoformat(expiry_date) - date.today()).days
            if days_left > 2:
                status = "fresh"
            elif days_left >= 1:
                status = "use_first"
            else:
                status = "check_item"
        else:  # no date known: no reminder
            days_left = None
            status = "fresh"

        items.append(
            {
                "id": id_,
                "ingredient_name": name,
                "quantity": quantity,
                "unit": unit,
                "purchase_date": purchase_date,
                "expiry_date": expiry_date,
                "days_left": days_left,
                "status": status,
                "source_receipt_id": receipt_id,
            }
        )
    return items


def save_confirmed_receipt(receipt, items):
    """Save a receipt the user confirmed. Returns True if saved, False if it was
    already saved (same store, date and total), so spending never counts twice."""
    conn = get_connection()
    try:
        already_saved = conn.execute(
            "SELECT 1 FROM Receipts WHERE store = ? AND purchase_date = ? AND total_price = ?",
            (receipt["store"], receipt["purchase_date"], receipt["total_price"]),
        ).fetchone()
        if already_saved:
            return False

        cursor = conn.execute(
            "INSERT INTO Receipts (store, purchase_date, total_price) VALUES (?, ?, ?)",
            (receipt["store"], receipt["purchase_date"], receipt["total_price"]),
        )
        receipt_id = cursor.lastrowid
        purchase_date = date.fromisoformat(receipt["purchase_date"])

        for item in items:
            name = item["ingredient_name"]
            # Only names from our fixed list count as recognized. Never invent items.
            recognized = bool(item["recognized"]) and name in INGREDIENTS
            conn.execute(
                "INSERT INTO ReceiptItems "
                "(receipt_id, ingredient_name, raw_text, price, recognized) "
                "VALUES (?, ?, ?, ?, ?)",
                (receipt_id, name if recognized else None, item["raw_text"],
                 item["price"], 1 if recognized else 0),
            )
            if recognized:  # unrecognized items are NOT added to the pantry
                expiry_date = purchase_date + timedelta(days=INGREDIENTS[name]["shelf_days"])
                conn.execute(
                    "INSERT INTO PantryItems (ingredient_name, quantity, unit, "
                    "purchase_date, expiry_date, source_receipt_id) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (name, item["quantity"], item["unit"], purchase_date.isoformat(),
                     expiry_date.isoformat(), receipt_id),
                )

        conn.commit()  # all-or-nothing: either everything is saved, or nothing
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_pantry_quantity(item_id, quantity):
    # TODO: update PantryItems.quantity (0 = used up). Must NOT delete the receipt.
    pass


def get_spending_summary():
    budget = get_preferences()["weekly_budget"]

    today = date.today()
    monday = today - timedelta(days=today.weekday())  # weekday(): Monday = 0
    sunday = monday + timedelta(days=6)

    conn = get_connection()
    spent = conn.execute(
        "SELECT COALESCE(SUM(total_price), 0) FROM Receipts "
        "WHERE purchase_date BETWEEN ? AND ?",
        (monday.isoformat(), sunday.isoformat()),
    ).fetchone()[0]
    conn.close()

    return {"budget": budget, "spent": round(spent, 2), "remaining": round(budget - spent, 2)}


if __name__ == "__main__":
    init_db()
    print("Database initialized:", DB_PATH)
