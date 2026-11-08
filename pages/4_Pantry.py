import html

import streamlit as st

from data.ingredients import INGREDIENTS
from db import get_pantry_items, init_db, update_pantry_quantity

st.set_page_config(page_title="Pantry · Food4U", page_icon="🥬", layout="wide")

st.markdown("""
<style>
.stApp { background: #fdf9f2; color: #111310; }
[data-testid="stHeader"], [data-testid="stToolbar"] { display: none; }
[data-testid="stMainBlockContainer"] { max-width: 1440px; padding: 20px 36px 55px; }

.stApp :is(p, label, input, button, h1, h2, h3, li, [data-testid="stMetricLabel"],
           [data-testid="stMetricValue"], [data-testid="stCaptionContainer"]) {
  font-family: Arial, Helvetica, sans-serif !important;
}
h1, h2, h3 { color: #111310; font-weight: 800 !important; }
h1 { font-size: clamp(44px, 5vw, 72px) !important; letter-spacing: -2.5px; line-height: 1.02 !important; }
h3 { font-size: 30px !important; letter-spacing: -1px; }
.stApp p { font-size: 18px; }
[data-testid="stPageLink"] a { color: #111310; font-weight: 700; font-size: 16px; }

.eyebrow { color: #4d5a2e; font-size: 13px; font-weight: 700; letter-spacing: 1.5px; margin: 0 0 4px; }

[class*="st-key-tile_"] button { border-radius: 18px; min-height: 56px; background: #e3e9ce; padding: 0.3rem 1rem; }
[class*="st-key-tile_"] button p { font-size: 22px; font-weight: 800; }
[class*="st-key-tile_"] button:hover { background: #f3d7a8; }
[class*="st-key-tile_"] button[kind="primary"], [class*="st-key-tile_"] button[kind="primary"]:hover,
[class*="st-key-tile_"] [data-testid="stBaseButton-primary"], [class*="st-key-tile_"] [data-testid="stBaseButton-primary"]:hover { background: #111310; }
[class*="st-key-tile_"] button[kind="primary"] p, [class*="st-key-tile_"] [data-testid="stBaseButton-primary"] p { color: #fdf9f2; }

[class*="st-key-pantry_card_"] { background: #e3e9ce; border: 2px solid #111310 !important; border-radius: 22px !important; padding: 16px !important; }
.p-head { display: flex; align-items: center; gap: 12px; margin-bottom: 6px; }
.p-emoji { width: 50px; height: 50px; flex-shrink: 0; display: flex; align-items: center; justify-content: center;
           font-size: 28px; line-height: 1; background: #f1f4dc; border: 2px solid #111310; border-radius: 14px; }
.p-name { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; line-height: 1.1; }
.p-qty { font-size: 17px; font-weight: 700; margin-top: 2px; }
.p-days { font-size: 15px; font-weight: 700; margin: 4px 0 2px; }
.p-dates { font-size: 13px; color: #4d5a2e; margin-bottom: 8px; }
.p-bar-label { font-size: 13px; font-weight: 700; margin-bottom: 3px; }
.p-bar { height: 14px; border: 2px solid #111310; border-radius: 999px; background: #efe6d2; overflow: hidden; margin-bottom: 10px; }
.p-bar-fill { height: 100%; background: #F5B7C5; }
.pill { display: inline-block; padding: 3px 14px; margin-right: 8px; border: 2px solid #111310; border-radius: 999px; font-size: 14px; font-weight: 800; }
.pill-fresh { background: #fdf9f2; color: #111310; }
.pill-use_first { background: #f6dfa4; color: #111310; }
.pill-check_item { background: #f2c4bb; color: #111310; }

[data-testid="stNumberInput"] label p { font-size: 15px; font-weight: 700; }
[data-testid="stNumberInput"] input { font-size: 20px; font-weight: 700; }
.stButton > button { border-radius: 999px; border: 2px solid #111310; color: #111310; background: #f1f4dc; font-size: 17px; font-weight: 800; padding: 0.5rem 1rem; }
.stButton > button:hover { background: #f3d7a8; border-color: #111310; color: #111310; }
[class*="st-key-update_"] button, [class*="st-key-update_"] button p { background: #111310; color: #fdf9f2; }
[class*="st-key-update_"] button:hover, [class*="st-key-update_"] button:hover p { background: #DA9233; color: #111310; }
</style>
""", unsafe_allow_html=True)

st.page_link("app.py", label="← Back to Home")

init_db()

PILL_TEXT = {"fresh": "Fresh", "use_first": "Use first", "check_item": "Check item"}

SECTIONS = [
    ("check_item", "Check these",
     "These items reached their reference date. Please check them. "
     "If they are no longer good, they can be thrown away."),
    ("use_first", "Use first", "Suggest using these first."),
    ("fresh", "Fresh", None),
]

CATEGORY_EMOJI = {
    "vegetable": "🥬", "fruit": "🍎", "meat": "🍗", "seafood": "🐟", "egg": "🥚",
    "protein": "🫘", "dairy": "🧀", "grain": "🌾", "legume": "🫘", "canned": "🥫",
    "condiment": "🧂", "spice": "🌶️", "oil": "🫒", "nut": "🥜", "sweet": "🍫",
}

INGREDIENT_EMOJI = {
    "tomato": "🍅", "onion": "🧅", "garlic": "🧄", "ginger": "🫚", "green_onion": "🌱", "potato": "🥔",
    "carrot": "🥕", "bell_pepper": "🫑", "broccoli": "🥦", "lettuce": "🥬", "bean_sprouts": "🌱",
    "cilantro": "🌿", "spinach": "🥬", "mushroom": "🍄", "cucumber": "🥒", "napa_cabbage": "🥬",
    "cabbage": "🥬", "bok_choy": "🥬",
    "lemon": "🍋", "lime": "🍋", "banana": "🍌", "avocado": "🥑",
    "chicken": "🍗", "ground_beef": "🥩", "ground_pork": "🥩", "beef": "🥩", "pork_ribs": "🍖", "bacon": "🥓",
    "salmon": "🐟", "shrimp": "🦐", "egg": "🥚", "tofu": "🫘",
    "milk": "🥛", "butter": "🧈", "cheese": "🧀", "parmesan": "🧀", "yogurt": "🥣", "cream": "🥛", "paneer": "🧀",
    "rice": "🍚", "pasta": "🍝", "rice_noodles": "🍜", "bread": "🍞", "burger_bun": "🍔", "flour": "🌾",
    "oats": "🥣", "corn_tortilla": "🌮", "flour_tortilla": "🫓", "naan": "🫓", "rice_paper": "🍘",
    "red_lentils": "🫘", "kidney_beans": "🫘", "canned_tomato": "🥫",
    "soy_sauce": "🍶", "fish_sauce": "🍶", "miso": "🥣", "doubanjiang": "🌶️", "gochujang": "🌶️",
    "kimchi": "🥬", "sesame_oil": "🫙", "sesame_seeds": "🌰", "dashi": "🍲", "curry_roux": "🍛",
    "mayonnaise": "🫙", "ketchup": "🥫", "caesar_dressing": "🥗", "maple_syrup": "🍁",
    "salt": "🧂", "sugar": "🍬", "black_pepper": "🧂", "curry_powder": "🍛", "garam_masala": "🌶️",
    "turmeric": "🧂", "chili_powder": "🌶️", "baking_powder": "🧁", "baking_soda": "🧁",
    "vegetable_oil": "🫙", "olive_oil": "🫒", "peanut": "🥜", "cashew": "🥜",
    "dark_chocolate": "🍫", "chocolate_chips": "🍫", "chocolate_truffles": "🍫", "marshmallow": "🍡",
}


def display_name(item):
    info = INGREDIENTS.get(item["ingredient_name"], {})
    return info.get("display_name", item["ingredient_name"])


def emoji_for(item):
    key = item["ingredient_name"]
    if key in INGREDIENT_EMOJI:
        return INGREDIENT_EMOJI[key]
    return CATEGORY_EMOJI.get(INGREDIENTS.get(key, {}).get("category"), "🍽️")


def days_text(days_left):
    if days_left is None:
        return "no reference date"
    if days_left < 0:
        return f"{-days_left} day(s) past"
    return f"{days_left} day(s) left"


def freshness(item):
    """Share of the shelf life that is left (0 to 1), or None if we cannot tell."""
    shelf_days = INGREDIENTS.get(item["ingredient_name"], {}).get("shelf_days")
    if item["days_left"] is None or not shelf_days:
        return None
    return max(0.0, min(1.0, item["days_left"] / shelf_days))


def render_card(item):
    name = display_name(item)
    unit = item["unit"] or ""

    with st.container(border=True, key=f"pantry_card_{item['id']}"):
        st.markdown(
            f'<div class="p-head"><div class="p-emoji">{emoji_for(item)}</div>'
            f'<div><div class="p-name">{html.escape(str(name))}</div>'
            f'<div class="p-qty">{item["quantity"]:g} {html.escape(unit)}</div></div></div>'
            f'<div class="p-days"><span class="pill pill-{item["status"]}">{PILL_TEXT[item["status"]]}</span>'
            f"{days_text(item['days_left'])}</div>"
            f'<div class="p-dates">Bought {item["purchase_date"]} · reference date {item["expiry_date"]}</div>',
            unsafe_allow_html=True,
        )

        left = freshness(item)
        if left is not None:
            st.markdown(
                f'<div class="p-bar-label">Freshness</div>'
                f'<div class="p-bar"><div class="p-bar-fill" style="width:{left * 100:.0f}%"></div></div>',
                unsafe_allow_html=True,
            )

        new_quantity = st.number_input(
            f"Change quantity ({unit})" if unit else "Change quantity",
            min_value=0.0,
            value=float(item["quantity"]),
            step=1.0,
            format="%g",
            key=f"qty_{item['id']}",
        )

        update_col, used_col = st.columns(2)
        with update_col:
            if st.button("Update", key=f"update_{item['id']}", use_container_width=True):
                update_pantry_quantity(item["id"], new_quantity)
                st.session_state["pantry_last"] = {
                    "message": f"Updated {name}: {item['quantity']:g} → {new_quantity:g} {unit}.",
                    "undo": (item["id"], item["quantity"]),
                    "undone": f"Undone: {name} is back to {item['quantity']:g} {unit}.",
                }
                st.rerun()
        with used_col:
            if st.button("Used up", key=f"used_{item['id']}", use_container_width=True):
                update_pantry_quantity(item["id"], 0)
                st.session_state["pantry_last"] = {
                    "message": f"{name} marked as used up.",
                    "undo": (item["id"], item["quantity"]),
                    "undone": f"Undone: {name} is back to {item['quantity']:g} {unit}.",
                }
                st.rerun()


st.markdown('<div class="eyebrow">YOUR EVERYDAY KITCHEN</div>', unsafe_allow_html=True)
st.title("Your pantry")
st.write("Everything you have at home, and what to use first.")

last_action = st.session_state.get("pantry_last")
if last_action:
    message_col, undo_col = st.columns([5, 1], vertical_alignment="center")
    message_col.success(last_action["message"])
    if last_action["undo"] and undo_col.button("Undo", key="undo_last", use_container_width=True):
        item_id, old_quantity = last_action["undo"]
        update_pantry_quantity(item_id, old_quantity)
        st.session_state["pantry_last"] = {"message": last_action["undone"], "undo": None}
        st.rerun()

items = get_pantry_items()

if not items:
    st.info("Your pantry is empty. Upload a receipt to add items.")
    st.page_link("pages/3_Receipt.py", label="Upload a receipt →", icon="🧾")
    st.stop()

def set_filter(status):
    # clicking the selected tile again shows everything
    st.session_state["pantry_filter"] = None if st.session_state.get("pantry_filter") == status else status


wanted = st.session_state.get("pantry_filter")
tiles = [
    ("tile_all", f"**{len(items)}** In your pantry", None),
    ("tile_fresh", f"**{sum(1 for i in items if i['status'] == 'fresh')}** Fresh", "fresh"),
    ("tile_use_first", f"**{sum(1 for i in items if i['status'] == 'use_first')}** Use first", "use_first"),
    ("tile_check", f"**{sum(1 for i in items if i['status'] == 'check_item')}** To check", "check_item"),
]
for col, (key, label, status) in zip(st.columns([1.3, 1.3, 1.3, 1.3, 1.8], gap="small"), tiles):
    col.button(label, key=key, use_container_width=True,
               type="primary" if wanted == status else "secondary",
               on_click=set_filter, args=(status,))

st.write("")

shown = False
for status, heading, note in SECTIONS:
    if wanted and status != wanted:
        continue
    group = [i for i in items if i["status"] == status]
    if not group:
        continue

    shown = True
    st.subheader(f"{heading} · {len(group)}")
    if note:
        st.caption(note)

    for start in range(0, len(group), 3):
        for col, item in zip(st.columns(3, gap="medium"), group[start:start + 3]):
            with col:
                render_card(item)

if not shown:
    st.info("Nothing here right now.")
