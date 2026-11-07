import sqlite3

DB_PATH = "food4u.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS UserPreferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuisine TEXT,
            weekly_budget REAL
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
    # TODO: read from UserPreferences
    return {
        "weekly_budget": 60.0,
        "cuisines": ["chinese", "japanese"],
        "spice_level": 2,
        "flavor": "savory",
        "avoid_tags": ["peanut"],
    }


def save_preferences(prefs):
    # TODO: write prefs to UserPreferences
    pass


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
