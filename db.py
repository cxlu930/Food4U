import os
import re
import sqlite3
from datetime import date, datetime, timedelta
from math import ceil
from zoneinfo import ZoneInfo

import streamlit as st

from data.ingredients import INGREDIENTS

DB_PATH = "food4u.db"

# Demo only: fill an empty pantry with sample items. Set to False to turn it off.
SEED_SAMPLE_DATA = False

# Budget. The weekly and monthly amounts are saved separately. The monthly default is its own
# number, NOT weekly x 4. A budget the user saved as 0 is kept as 0.
DEFAULT_WEEKLY_BUDGET = 100.0
DEFAULT_MONTHLY_BUDGET = 400.0
BUDGET_PERIODS = ("weekly", "monthly")


def today_vancouver():
    """Today's date in Vancouver. The server may run in another time zone (Streamlit Cloud uses UTC),
    and weeks and months must start on the Vancouver calendar."""
    try:
        return datetime.now(ZoneInfo("America/Vancouver")).date()
    except Exception:  # no time zone data installed: fall back to the server's date
        return date.today()


_schema_ready = False


def get_connection():
    # The first connection (or the first after food4u.db was deleted) makes sure the tables exist,
    # so it does not matter which page a visitor opens first.
    global _schema_ready
    if not _schema_ready or not os.path.exists(DB_PATH):
        _schema_ready = True  # set first: init_db() connects too
        try:
            init_db()
        except Exception:
            _schema_ready = False
            raise
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

    st.markdown("""
    <style>
    .stApp:has(.st-key-food4u_login) { background:#FAF8F0; color:#111310; }
    body:has(.st-key-food4u_login) [data-testid="stHeader"],
    body:has(.st-key-food4u_login) [data-testid="stToolbar"],
    body:has(.st-key-food4u_login) [data-testid="stSidebar"],
    body:has(.st-key-food4u_login) [data-testid="stSidebarCollapsedControl"] { display:none; }
    body:has(.st-key-food4u_login) [data-testid="stMainBlockContainer"] {
      width:100%; max-width:488px; min-height:100vh; min-height:100svh;
      padding:40px 24px; display:flex; flex-direction:column; justify-content:center;
    }
    body:has(.st-key-food4u_login) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { width:100%; gap:0; }
    .st-key-food4u_login { width:100%; max-width:440px; margin:0 auto; gap:0; font-family:Arial,Helvetica,sans-serif; }
    .st-key-food4u_login .login-brand { display:flex; justify-content:center; align-items:center; gap:9px; margin-bottom:40px; font-size:25px; font-weight:800; letter-spacing:-.7px; color:#111310; }
    .st-key-food4u_login .login-brand svg { width:34px; height:34px; }
    .st-key-food4u_login h1 { font-family:Arial,Helvetica,sans-serif !important; text-align:center; font-size:clamp(38px,8vw,48px) !important; font-weight:800 !important; letter-spacing:-1.8px; line-height:1.15 !important; color:#111310; margin:0 !important; padding:0 !important; }
    .st-key-food4u_login .login-subtitle { text-align:center; color:#79806d; font-size:16px; margin:14px 0 36px; }
    .st-key-food4u_login [data-testid="stForm"] { border:0 !important; padding:0 !important; background:transparent; }
    .st-key-food4u_login [data-testid="stForm"] [data-testid="stVerticalBlock"] { gap:18px; }
    .st-key-food4u_login [data-testid="stWidgetLabel"] p { font-family:Arial,Helvetica,sans-serif; color:#283021; font-size:13px; font-weight:700; }
    .st-key-food4u_login [data-baseweb="input"] { background:#fff; border:1px solid #dedfd5; border-radius:13px; box-shadow:none; }
    .st-key-food4u_login [data-baseweb="input"]:focus-within { border-color:#9cbd40; box-shadow:0 0 0 2px #b8e63d33; }
    .st-key-food4u_login input { color:#111310; font-family:Arial,Helvetica,sans-serif; font-size:15px; padding:14px 15px; }
    .st-key-food4u_login input::placeholder { color:#919687; }
    .st-key-food4u_login [data-testid="stFormSubmitButton"] button { width:100%; min-height:50px; border:1px solid #B8E63D; border-radius:999px; background:#B8E63D; color:#111310; font-family:Arial,Helvetica,sans-serif; font-weight:750; box-shadow:none; }
    .st-key-food4u_login [data-testid="stFormSubmitButton"] button p { font-weight:750; }
    .st-key-food4u_login [data-testid="stFormSubmitButton"] button:hover { background:#abd535; border-color:#abd535; color:#111310; }
    .st-key-food4u_login [data-testid="stFormSubmitButton"] button:focus-visible { outline:2px solid #718e2c; outline-offset:3px; }
    .st-key-food4u_login .login-footer { text-align:center; font-size:10px; letter-spacing:2px; color:#8b927d; margin:36px 0 0; }
    @media(min-width:769px) {
      .st-key-food4u_login h1 {
        width:min(960px, calc(100vw - 48px)); position:relative;
        left:50%; transform:translateX(-50%); white-space:nowrap;
        font-size:clamp(30px, 4.4vw, 48px) !important;
      }
    }
    @media(max-width:480px) {
      body:has(.st-key-food4u_login) [data-testid="stMainBlockContainer"] { padding:32px 24px; }
      .st-key-food4u_login .login-brand { margin-bottom:32px; }
    }
    </style>
    """, unsafe_allow_html=True)
    with st.container(key="food4u_login"):
        st.markdown('''<div class="login-brand">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 44" fill="none" stroke="#B8E63D" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M7 30C-2 12 13 5 34 3c0 19-6 31-22 27" fill="#B8E63D" stroke="none"/>
            <path d="M3 36 27 12"/><path d="m10 28 15-15" stroke="#FAF8F0"/>
          </svg><span>FOOD4U</span></div>''', unsafe_allow_html=True)
        st.title("Your Food. Your Budget. Your Way.")
        st.markdown('<p class="login-subtitle">Good to have you here.</p>', unsafe_allow_html=True)
        with st.form("food4u_nickname", border=False):
            nickname = st.text_input("Nickname", max_chars=30, placeholder="What should we call you?")
            start = st.form_submit_button("Let's get cooking →", use_container_width=True)
        st.markdown('<p class="login-footer">GOOD FOOD, LESS FUSS.</p>', unsafe_allow_html=True)
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


def _add_budget_columns(conn):
    """Databases from before the monthly budget get the two new columns. Nothing is lost."""
    cols = [row[1] for row in conn.execute("PRAGMA table_info(UserPreferences)")]
    if cols and "budget_period" not in cols:
        conn.execute("ALTER TABLE UserPreferences ADD COLUMN budget_period TEXT NOT NULL DEFAULT 'weekly'")
    if cols and "monthly_budget" not in cols:
        conn.execute("ALTER TABLE UserPreferences ADD COLUMN monthly_budget REAL")  # NULL = never set


def init_db():
    conn = sqlite3.connect(DB_PATH)  # not get_connection(): that calls init_db()
    _migrate_to_users(conn)
    _add_budget_columns(conn)
    conn.executescript(
        """
        -- One row per visitor (their nickname).
        CREATE TABLE IF NOT EXISTS UserPreferences (
            user_id TEXT PRIMARY KEY,
            weekly_budget REAL,
            cuisines TEXT,               -- comma-separated, e.g. "chinese,japanese"
            spice_level INTEGER,         -- 0 none, 1 mild, 2 medium, 3 hot
            flavor TEXT,                 -- comma-separated TASTES, e.g. "savory,sour"; empty = no preference
            avoid_tags TEXT,             -- comma-separated allergy / diet tags
            budget_period TEXT NOT NULL DEFAULT 'weekly',   -- 'weekly' or 'monthly'
            monthly_budget REAL          -- NULL = never set (the default is used)
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

        -- recipe_id is the "id" of a recipe in data/recipes.json. One row per visitor and recipe.
        CREATE TABLE IF NOT EXISTS Favorites (
            user_id TEXT NOT NULL,
            recipe_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (user_id, recipe_id)
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
    today = today_vancouver()
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
        "SELECT weekly_budget, cuisines, spice_level, flavor, avoid_tags, budget_period, monthly_budget "
        "FROM UserPreferences WHERE user_id = ?",
        (uid,),
    ).fetchone()
    conn.close()

    if row is None:  # never saved: default 100 CAD a week, 400 a month, spice 0. A saved 0 stays 0.
        return {
            "weekly_budget": DEFAULT_WEEKLY_BUDGET,
            "monthly_budget": DEFAULT_MONTHLY_BUDGET,
            "budget_period": "weekly",
            "cuisines": [],
            "spice_level": 0,
            "flavor": [],
            "avoid_tags": [],
        }

    weekly_budget, cuisines, spice_level, flavor, avoid_tags, budget_period, monthly_budget = row
    return {
        "weekly_budget": weekly_budget,
        "monthly_budget": DEFAULT_MONTHLY_BUDGET if monthly_budget is None else monthly_budget,
        "budget_period": budget_period if budget_period in BUDGET_PERIODS else "weekly",
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
    # Older pages do not send budget_period / monthly_budget: whatever is left out keeps its saved
    # value (a page that only saves the weekly budget must not wipe the monthly one).
    old = conn.execute(
        "SELECT weekly_budget, budget_period, monthly_budget FROM UserPreferences WHERE user_id = ?",
        (uid,),
    ).fetchone() or (None, "weekly", None)
    old_weekly, old_period, old_monthly = old
    weekly = prefs["weekly_budget"] if "weekly_budget" in prefs else (
        DEFAULT_WEEKLY_BUDGET if old_weekly is None else old_weekly
    )
    monthly = prefs["monthly_budget"] if "monthly_budget" in prefs else old_monthly  # None = never set
    period = prefs.get("budget_period", old_period)
    if period not in BUDGET_PERIODS:
        conn.close()
        raise ValueError(f"budget_period must be one of {BUDGET_PERIODS}, not {period!r}")

    # INSERT OR REPLACE overwrites this visitor's row (user_id is the primary key).
    conn.execute(
        "INSERT OR REPLACE INTO UserPreferences "
        "(user_id, weekly_budget, cuisines, spice_level, flavor, avoid_tags, budget_period, monthly_budget) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            uid,
            weekly,
            ",".join(prefs["cuisines"]),
            prefs["spice_level"],
            ",".join(f for f in flavor if f and f != "no_preference"),
            ",".join(prefs["avoid_tags"]),
            period,
            monthly,
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
            days_left = (date.fromisoformat(expiry_date) - today_vancouver()).days
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


def _period_range(period, today):
    """First and last day of the week (Monday to Sunday) or of the calendar month containing today."""
    if period == "monthly":
        start = today.replace(day=1)
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start, next_month - timedelta(days=1)
    start = today - timedelta(days=today.weekday())
    return start, start + timedelta(days=6)


def get_budget_summary(period=None, user_id=None):
    """Budget, spending and what is left for a period. `period` is 'weekly' or 'monthly'; leave it out
    to use the one the user chose. Spending is the total of the receipts the user confirmed whose
    purchase date falls in the period (Vancouver calendar): it is never weekly spending x 4.

    Returns: period, budget, spent, remaining, start_date, end_date (YYYY-MM-DD), days_left (counting
    today) and plan_budget: what one week of meal planning may cost. Weekly: the remaining budget.
    Monthly: the remaining budget divided by the weeks left in the month (at least 1)."""
    uid = _uid(user_id)
    prefs = get_preferences(uid)
    period = period or prefs["budget_period"]
    if period not in BUDGET_PERIODS:
        raise ValueError(f"period must be one of {BUDGET_PERIODS}, not {period!r}")
    budget = prefs["monthly_budget"] if period == "monthly" else prefs["weekly_budget"]

    today = today_vancouver()
    start, end = _period_range(period, today)

    conn = get_connection()
    spent = conn.execute(
        "SELECT COALESCE(SUM(total_price), 0) FROM Receipts "
        "WHERE user_id = ? AND purchase_date BETWEEN ? AND ?",
        (uid, start.isoformat(), end.isoformat()),
    ).fetchone()[0]
    conn.close()

    remaining = round(budget - spent, 2)
    days_left = (end - today).days + 1
    weeks_left = max(1, ceil(days_left / 7))
    return {
        "period": period,
        "budget": budget,
        "spent": round(spent, 2),
        "remaining": remaining,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "days_left": days_left,
        "plan_budget": remaining if period == "weekly" else round(remaining / weeks_left, 2),
    }


def get_receipts(start_date, end_date, user_id=None):
    """The user's confirmed receipts whose purchase date is from start_date to end_date (both included).
    Dates can be date objects or YYYY-MM-DD text. Used by the Budget Summary page.

    Returns a list, oldest first. Each receipt: id, store, purchase_date (YYYY-MM-DD), total_price and
    items: a list of {ingredient_name (None if unrecognized), raw_text, price, recognized (True/False)}."""
    uid = _uid(user_id)
    start = start_date if isinstance(start_date, str) else start_date.isoformat()
    end = end_date if isinstance(end_date, str) else end_date.isoformat()

    conn = get_connection()
    receipts = [
        {"id": row[0], "store": row[1], "purchase_date": row[2], "total_price": row[3] or 0.0, "items": []}
        for row in conn.execute(
            "SELECT id, store, purchase_date, total_price FROM Receipts "
            "WHERE user_id = ? AND purchase_date BETWEEN ? AND ? ORDER BY purchase_date, id",
            (uid, start, end),
        ).fetchall()
    ]
    by_id = {receipt["id"]: receipt for receipt in receipts}
    for receipt_id, name, raw_text, price, recognized in conn.execute(
        "SELECT ri.receipt_id, ri.ingredient_name, ri.raw_text, ri.price, ri.recognized "
        "FROM ReceiptItems ri JOIN Receipts r ON r.id = ri.receipt_id "
        "WHERE r.user_id = ? AND r.purchase_date BETWEEN ? AND ? ORDER BY ri.id",
        (uid, start, end),
    ).fetchall():
        by_id[receipt_id]["items"].append({
            "ingredient_name": name, "raw_text": raw_text, "price": price, "recognized": bool(recognized),
        })
    conn.close()
    return receipts


def get_spending_summary(user_id=None):
    """The WEEKLY summary, kept for code written before the monthly budget (Home, the recommender).
    budget, spent and remaining are unchanged; the other keys are new. For the period the user
    chose, use get_budget_summary()."""
    return get_budget_summary("weekly", user_id)


def add_favorite(recipe_id, user_id=None):
    """Save a recipe as a favorite. Saving it twice is fine."""
    uid = _uid(user_id)
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO Favorites (user_id, recipe_id, created_at) VALUES (?, ?, ?)",
        (uid, int(recipe_id), datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def remove_favorite(recipe_id, user_id=None):
    uid = _uid(user_id)
    conn = get_connection()
    conn.execute("DELETE FROM Favorites WHERE user_id = ? AND recipe_id = ?", (uid, int(recipe_id)))
    conn.commit()
    conn.close()


def get_favorites(user_id=None):
    """recipe_id of every favorite, the most recently saved first."""
    uid = _uid(user_id)
    conn = get_connection()
    rows = conn.execute(
        "SELECT recipe_id FROM Favorites WHERE user_id = ? ORDER BY created_at DESC, rowid DESC", (uid,)
    ).fetchall()
    conn.close()
    return [row[0] for row in rows]


if __name__ == "__main__":
    init_db()
    print("Database initialized:", DB_PATH)
