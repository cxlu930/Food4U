import streamlit as st

from data.ingredients import INGREDIENTS
from db import get_pantry_items, init_db, update_pantry_quantity

st.set_page_config(layout="wide")

init_db()

STATUS_LABELS = {
    "fresh": ":green[Fresh]",
    "use_first": ":orange[Use first]",
    "check_item": ":red[Check item]",
}


def display_name(item):
    info = INGREDIENTS.get(item["ingredient_name"], {})
    return info.get("display_name", item["ingredient_name"])


def days_text(days_left):
    if days_left is None:
        return "no reference date"
    if days_left < 0:
        return f"{-days_left} day(s) past"
    return f"{days_left} day(s) left"


st.title("Pantry")

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
    st.stop()

use_first = [i for i in items if i["status"] == "use_first"]
check_item = [i for i in items if i["status"] == "check_item"]

if use_first:
    lines = [f"- {display_name(i)} ({days_text(i['days_left'])})" for i in use_first]
    st.warning("Suggest using first:\n" + "\n".join(lines))

if check_item:
    lines = [f"- {display_name(i)} ({days_text(i['days_left'])})" for i in check_item]
    st.error(
        "These items reached their reference date. Please check them. "
        "If they are no longer good, they can be thrown away:\n" + "\n".join(lines)
    )

st.subheader("Your items")

for item in items:
    name = display_name(item)
    unit = item["unit"] or ""

    with st.container(border=True):
        st.markdown(f"**{name}** · {item['quantity']:g} {unit}")
        st.caption(
            f"{STATUS_LABELS[item['status']]} · bought {item['purchase_date']} · "
            f"reference date {item['expiry_date']} ({days_text(item['days_left'])})"
        )

        qty_col, update_col, used_col = st.columns([2, 1, 1], vertical_alignment="bottom")

        with qty_col:
            new_quantity = st.number_input(
                f"Change quantity ({unit})" if unit else "Change quantity",
                min_value=0.0,
                value=float(item["quantity"]),
                step=1.0,
                format="%g",
                key=f"qty_{item['id']}",
            )

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
