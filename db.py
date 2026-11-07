import sqlite3

DB_PATH = "food4u.db"


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
            flavor TEXT,                 -- sweet / savory / no_preference
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
            expiry_date TEXT,
            source_receipt_id INTEGER
        );
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Data functions for A, B, C. Shapes follow docs/data-contract.md.
# FIRST VERSION: returns fake data, no SQL yet. TODO: replace with real SQL.
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
            "flavor": "no_preference",
            "avoid_tags": [],
        }

    weekly_budget, cuisines, spice_level, flavor, avoid_tags = row
    return {
        "weekly_budget": weekly_budget,
        # "a,b" -> ["a", "b"]; empty string -> []
        "cuisines": [c for c in (cuisines or "").split(",") if c],
        "spice_level": spice_level,
        "flavor": flavor,
        "avoid_tags": [t for t in (avoid_tags or "").split(",") if t],
    }


def save_preferences(prefs):
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
            prefs["flavor"],
            ",".join(prefs["avoid_tags"]),
        ),
    )
    conn.commit()
    conn.close()


def get_pantry_items():
    # TODO: read from PantryItems and compute days_left / status
    return [
        {
            "id": 1,
            "ingredient_name": "tomato",
            "quantity": 3.0,
            "unit": "pcs",
            "purchase_date": "2026-11-05",
            "expiry_date": "2026-11-12",
            "days_left": 5,
            "status": "fresh",
            "source_receipt_id": 1,
        },
        {
            "id": 2,
            "ingredient_name": "chicken",
            "quantity": 500.0,
            "unit": "g",
            "purchase_date": "2026-11-05",
            "expiry_date": "2026-11-08",
            "days_left": 1,
            "status": "use_first",
            "source_receipt_id": 1,
        },
        {
            "id": 3,
            "ingredient_name": "milk",
            "quantity": 1.0,
            "unit": "L",
            "purchase_date": "2026-10-28",
            "expiry_date": "2026-11-04",
            "days_left": -3,
            "status": "check_item",
            "source_receipt_id": None,
        },
    ]


def save_confirmed_receipt(receipt, items):
    # TODO: insert Receipts + ReceiptItems, add recognized items to PantryItems,
    # and do nothing if this receipt was already saved.
    pass


def update_pantry_quantity(item_id, quantity):
    # TODO: update PantryItems.quantity (0 = used up). Must NOT delete the receipt.
    pass


def get_spending_summary():
    # TODO: budget from UserPreferences, spent = this week's Receipts.total_price
    return {"budget": 60.0, "spent": 23.4, "remaining": 36.6}


if __name__ == "__main__":
    init_db()
    print("Database initialized:", DB_PATH)
