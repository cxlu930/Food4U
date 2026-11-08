import re
import sqlite3
from datetime import date, timedelta

import streamlit as st

from data.ingredients import INGREDIENTS

DB_PATH = "food4u.db"

# Demo only: fill an empty pantry with sample items. Set to False to turn it off.
SEED_SAMPLE_DATA = False


def get_connection():
    return sqlite3.connect(DB_PATH)


def clean_nickname(text):
    """Lowercase, keep letters, digits, spaces, - and _ (any language). '' if nothing is left."""
    text = re.sub(r"[^\w -]", "", (text or "").lower())
    return re.sub(r"\s+", " ", text).strip()[:30]


def current_user():
    """Nickname of the current visitor, or None if they have not entered one yet."""
    name = st.session_state.get("nickname")
    if not name:
        name = clean_nickname(st.query_params.get("u", ""))
        if name:
            st.session_state["nickname"] = name
    return name or None


def require_user():
    """Return the current nickname. With no nickname yet, show the nickname form and stop the page."""
    name = current_user()
    if name:
        if st.query_params.get("u") != name:
            st.query_params["u"] = name  # keep the nickname in the URL so a reload keeps it
        return name

    st.title("Welcome to Food4U")
    st.write(
        "Type a nickname to get your own preferences, pantry and budget. "
        "Use the same nickname next time to see them again."
    )
    with st.form("food4u_nickname"):
        nickname = st.text_input("Nickname", max_chars=30)
        start = st.form_submit_button("Start")
    if start:
        name = clean_nickname(nickname)
        if name:
            st.session_state["nickname"] = name
            st.query_params["u"] = name
            st.rerun()
        st.error("Please type a nickname with letters or numbers.")
    st.stop()


def sign_out():
    st.session_state.pop("nickname", None)
    st.query_params.clear()
    st.rerun()


def _uid(user_id=None):
    # Pages never pass user_id: it is the current visitor. Tests and scripts can pass one.
    return user_id or require_user()


def _migrate_to_users(conn):
    """Old databases have no user_id. Upgrade them in place so nobody has to delete food4u.db."""

    def columns(table):
        return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]

    prefs = columns("UserPreferences")
    if prefs and "user_id" not in prefs:
        conn.execute("DROP TABLE UserPreferences")  # old single-row table, recreated below
    for table in ("Receipts", "PantryItems"):
        cols = columns(table)
        if cols and "user_id" not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN user_id TEXT NOT NULL DEFAULT 'guest'")


def init_db():
    conn = get_connection()
    _migrate_to_users(conn)
    conn.executescript(
        """
        -- One row per visitor (their nickname).
        CREATE TABLE IF NOT EXISTS UserPreferences (
            user_id TEXT PRIMARY KEY,
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
            user_id TEXT NOT NULL DEFAULT 'guest',
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
            user_id TEXT NOT NULL DEFAULT 'guest',
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
        ("tomato", 4, "pcs", 2, 5),
        ("rice", 2, "kg", 10, 300),
        ("onion", 3, "pcs", 3, 27),
        ("garlic", 2, "pcs", 5, 40),
        ("carrot", 5, "pcs", 4, 15),
        ("chicken", 500, "g", 6, 1),
        ("egg", 6, "pcs", 10, 2),
        ("spinach", 200, "g", 5, 0),
        ("milk", 1, "L", 9, -2),
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
# ---------------------------------------------------------------------------


def get_preferences(user_id=None):
    uid = _uid(user_id)
    conn = get_connection()
    row = conn.execute(
        "SELECT weekly_budget, cuisines, spice_level, flavor, avoid_tags "
        "FROM UserPreferences WHERE user_id = ?",
        (uid,),
    ).fetchone()
    conn.close()

    if row is None:  # never saved: default 100 CAD, spice 0. A saved 0 is read as it is.
        return {
            "weekly_budget": 100.0,
            "cuisines": [],
            "spice_level": 0,
            "flavor": [],
            "avoid_tags": [],
        }

    weekly_budget, cuisines, spice_level, flavor, avoid_tags = row
    return {
        "weekly_budget": weekly_budget,
        "cuisines": [c for c in (cuisines or "").split(",") if c],
        "spice_level": spice_level,
        "flavor": [f for f in (flavor or "").split(",") if f and f != "no_preference"],
        "avoid_tags": [t for t in (avoid_tags or "").split(",") if t],
    }


def save_preferences(prefs, user_id=None):
    uid = _uid(user_id)
    flavor = prefs["flavor"]
    if isinstance(flavor, str):  # accept "savory,sour" too, in case a page still sends text
        flavor = flavor.split(",")

    conn = get_connection()
    # INSERT OR REPLACE overwrites this visitor's row (user_id is the primary key).
    conn.execute(
        "INSERT OR REPLACE INTO UserPreferences "
        "(user_id, weekly_budget, cuisines, spice_level, flavor, avoid_tags) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            uid,
            prefs["weekly_budget"],
            ",".join(prefs["cuisines"]),
            prefs["spice_level"],
            ",".join(f for f in flavor if f and f != "no_preference"),
            ",".join(prefs["avoid_tags"]),
        ),
    )
    conn.commit()
    conn.close()


def get_pantry_items(user_id=None):
    uid = _uid(user_id)
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, ingredient_name, quantity, unit, purchase_date, expiry_date, "
        "source_receipt_id FROM PantryItems "
        "WHERE quantity > 0 AND user_id = ? "
        "ORDER BY expiry_date IS NULL, expiry_date",
        (uid,),
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


def save_confirmed_receipt(receipt, items, user_id=None):
    """Save a receipt the user confirmed. Returns True if saved, False if this visitor already
    saved it (same store, date and total), so spending never counts twice."""
    uid = _uid(user_id)
    conn = get_connection()
    try:
        already_saved = conn.execute(
            "SELECT 1 FROM Receipts WHERE user_id = ? AND store = ? AND purchase_date = ? AND total_price = ?",
            (uid, receipt["store"], receipt["purchase_date"], receipt["total_price"]),
        ).fetchone()
        if already_saved:
            return False

        cursor = conn.execute(
            "INSERT INTO Receipts (user_id, store, purchase_date, total_price) VALUES (?, ?, ?, ?)",
            (uid, receipt["store"], receipt["purchase_date"], receipt["total_price"]),
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
                    "INSERT INTO PantryItems (user_id, ingredient_name, quantity, unit, "
                    "purchase_date, expiry_date, source_receipt_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (uid, name, item["quantity"], item["unit"], purchase_date.isoformat(),
                     expiry_date.isoformat(), receipt_id),
                )

        conn.commit()  # all-or-nothing: either everything is saved, or nothing
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_pantry_quantity(item_id, quantity, user_id=None):
    """Set the quantity of one of this visitor's pantry items. 0 = used up (hidden, but the row
    stays). Only touches PantryItems, never Receipts."""
    uid = _uid(user_id)
    quantity = max(quantity, 0)
    conn = get_connection()
    conn.execute(
        "UPDATE PantryItems SET quantity = ? WHERE id = ? AND user_id = ?", (quantity, item_id, uid)
    )
    conn.commit()
    conn.close()


def get_spending_summary(user_id=None):
    uid = _uid(user_id)
    budget = get_preferences(uid)["weekly_budget"]

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    conn = get_connection()
    spent = conn.execute(
        "SELECT COALESCE(SUM(total_price), 0) FROM Receipts "
        "WHERE user_id = ? AND purchase_date BETWEEN ? AND ?",
        (uid, monday.isoformat(), sunday.isoformat()),
    ).fetchone()[0]
    conn.close()

    return {"budget": budget, "spent": round(spent, 2), "remaining": round(budget - spent, 2)}


if __name__ == "__main__":
    init_db()
    print("Database initialized:", DB_PATH)
