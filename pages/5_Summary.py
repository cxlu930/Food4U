"""Budget Summary: budget overview, spending by category, and weekly spending this month.

All numbers come from confirmed receipts (Receipts / ReceiptItems), never from the current pantry.
"""
from datetime import timedelta
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from data.ingredients import INGREDIENTS
from db import DEFAULT_MONTHLY_BUDGET, get_preferences, get_receipts, require_user, today_vancouver
from services.recommender import DEFAULT_WEEKLY_BUDGET

st.set_page_config(page_title="Budget Summary · Food4U", page_icon="📊", layout="wide")

require_user()  # know who this is from the first moment, so "Back to Home" keeps the nickname

GREEN, YELLOW, RED = "#9DBD43", "#E3B23C", "#C8553D"

st.markdown(
    """
<style>
.stApp { background:#fdf9f2; color:#111310; }
[data-testid="stHeader"], [data-testid="stToolbar"] { display:none; }
[data-testid="stMainBlockContainer"] { max-width:1100px; padding:20px 36px 55px; }
.stApp :is(p, label, button, h1, h2, h3, [data-testid="stMetricLabel"],
           [data-testid="stMetricValue"], [data-testid="stCaptionContainer"]) {
  font-family:Arial, Helvetica, sans-serif !important;
}
h1, h2, h3 { color:#111310; font-weight:800 !important; }
h1 { font-size:clamp(40px, 5vw, 64px) !important; letter-spacing:-2px; line-height:1.05 !important; }
h3 { font-size:clamp(22px, 3vw, 28px) !important; letter-spacing:-0.5px; }
[data-testid="stPageLink"] a { color:#405326; font-weight:700; }
[class*="st-key-summary_card_"] { background:#f5f7e9; border:1px solid #d9dfc8 !important;
  border-radius:22px !important; padding:20px 22px !important; }
[data-testid="stMetricValue"] { font-size:clamp(26px, 4vw, 36px) !important; font-weight:800; }
.f4u-bar { height:14px; border-radius:999px; background:#e3e6d6; overflow:hidden; margin:6px 0 4px; }
.f4u-bar > div { height:100%; border-radius:999px; }
.f4u-bar-label { display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;
  font:14px Arial, Helvetica, sans-serif; color:#52623a; }
[data-testid="stButtonGroup"] button { border-radius:999px !important; min-height:44px; }
@media (max-width:760px) {
  [data-testid="stMainBlockContainer"] { padding:18px 16px 40px; }
  [class*="st-key-summary_card_"] { padding:16px !important; }
}
</style>
""",
    unsafe_allow_html=True,
)


def resolve_budget(value, default):
    """Same rule as the recommender: only None or "" means "not set"; 0 is a real budget."""
    if value is None or value == "":
        return float(default), True
    return float(value), False


def period_range(period, today):
    if period == "monthly":
        start = today.replace(day=1)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        return start, end
    start = today - timedelta(days=today.weekday())
    return start, start + timedelta(days=6)


def money(value):
    return f"-${abs(value):,.2f}" if value < 0 else f"${value:,.2f}"


def short_date(day):
    return f"{day:%b} {day.day}"


def progress_html(spent, budget):
    """Progress bar: green, yellow above 80 %, red above 100 %. Works for a 0 budget."""
    if budget > 0:
        share = spent / budget
        label = f"{share:.0%} of budget used"
    else:
        share = 1.01 if spent > 0 else 0.0  # any spending is over a $0 budget
        label = "Budget is $0: any spending is over budget" if spent > 0 else "Budget is $0"
    color = RED if share > 1 else YELLOW if share > 0.8 else GREEN
    width = min(share, 1) * 100
    status = "Over budget" if share > 1 else "Close to the limit" if share > 0.8 else "On track"
    return (
        f'<div class="f4u-bar" role="progressbar" aria-valuenow="{width:.0f}" aria-valuemin="0" '
        f'aria-valuemax="100" aria-label="{escape(label)}"><div style="width:{width:.2f}%;background:{color}"></div></div>'
        f'<div class="f4u-bar-label"><span>{escape(label)}</span><span>{status}</span></div>'
    )


# ---------- Data ----------
prefs = get_preferences()
weekly_budget, weekly_is_default = resolve_budget(prefs.get("weekly_budget"), DEFAULT_WEEKLY_BUDGET)
monthly_budget, monthly_is_default = resolve_budget(prefs.get("monthly_budget"), DEFAULT_MONTHLY_BUDGET)

today = today_vancouver()
week_start, week_end = period_range("weekly", today)
month_start, month_end = period_range("monthly", today)
# One read covers both the current week and the current month (a week can start last month).
receipts = get_receipts(min(week_start, month_start), max(week_end, month_end))

# ---------- Header ----------
st.page_link("app.py", label="← Back to Home")
st.title("Budget Summary")

labels = {"weekly": "Weekly", "monthly": "Monthly"}
saved_period = prefs.get("budget_period") if prefs.get("budget_period") in labels else "weekly"
choice = st.segmented_control(
    "Period", list(labels.values()), default=labels[saved_period],
    label_visibility="collapsed", key="summary_period",
) or labels[saved_period]  # clicking the selected option again clears it: fall back
period = "monthly" if choice == "Monthly" else "weekly"

start, end = (month_start, month_end) if period == "monthly" else (week_start, week_end)
budget, using_default = (monthly_budget, monthly_is_default) if period == "monthly" else (weekly_budget, weekly_is_default)
in_period = [r for r in receipts if start.isoformat() <= r["purchase_date"] <= end.isoformat()]
spent = round(sum(r["total_price"] for r in in_period), 2)
remaining = round(budget - spent, 2)

st.caption(f"{choice} view · {short_date(start)} – {short_date(end)}, {end.year} · from your confirmed receipts")

# ---------- a) Budget overview ----------
with st.container(key="summary_card_overview"):
    st.subheader(f"{choice} budget")
    budget_col, spent_col, remaining_col = st.columns(3)
    budget_col.metric("Budget", money(budget))
    spent_col.metric("Spent", money(spent))
    remaining_col.metric(
        "Remaining", money(remaining),
        delta="Over budget" if remaining < 0 else None, delta_color="inverse",
    )
    st.markdown(progress_html(spent, budget), unsafe_allow_html=True)
    if using_default:
        st.caption(f"Using the default {period} budget of {money(budget)}. Set your own in Preferences.")

if not receipts:
    st.info(
        "No receipts yet for this week or month. Upload a receipt and confirm it, "
        "and your spending will show up here."
    )
    st.page_link("pages/3_Receipt.py", label="Upload a receipt →", icon="🧾")
    st.stop()

# ---------- b) Spending by category ----------
with st.container(key="summary_card_category"):
    st.subheader("Spending by category")
    totals = {}
    for receipt in in_period:
        for item in receipt["items"]:
            name = item["ingredient_name"]
            known = item["recognized"] and name in INGREDIENTS
            category = INGREDIENTS[name]["category"].replace("_", " ").title() if known else "Other"
            totals[category] = totals.get(category, 0.0) + (item["price"] or 0.0)
    category_df = pd.DataFrame(
        [{"Category": k, "Spent": round(v, 2)} for k, v in totals.items() if v > 0]
    )
    if category_df.empty:
        st.info(f"No item prices recorded for this {'month' if period == 'monthly' else 'week'} yet.")
    else:
        category_df = category_df.sort_values("Spent", ascending=False)
        category_df["Share"] = category_df["Spent"] / category_df["Spent"].sum()
        bars = alt.Chart(category_df).mark_bar(cornerRadiusEnd=6, color=GREEN).encode(
            x=alt.X("Spent:Q", title="Spent (CAD)", axis=alt.Axis(format="$,.0f", tickMinStep=1)),
            y=alt.Y("Category:N", sort="-x", title=None, axis=alt.Axis(labelLimit=120)),
            tooltip=[
                alt.Tooltip("Category:N"),
                alt.Tooltip("Spent:Q", format="$,.2f"),
                alt.Tooltip("Share:Q", format=".0%"),
            ],
        )
        text = bars.mark_text(align="left", dx=4, color="#111310").encode(
            text=alt.Text("Spent:Q", format="$,.2f")
        )
        chart = (bars + text).properties(height=max(160, 34 * len(category_df))).configure_view(stroke=None)
        st.altair_chart(chart, width="stretch")
        st.caption("Based on item prices. Unrecognized items count as Other. Receipt totals may also include tax.")

# ---------- c) Weekly spending this month ----------
with st.container(key="summary_card_weekly"):
    st.subheader(f"Weekly spending in {today:%B}")
    weeks = []
    first_monday = month_start - timedelta(days=month_start.weekday())
    monday = first_monday
    while monday <= month_end:
        w_start, w_end = max(monday, month_start), min(monday + timedelta(days=6), month_end)
        label = short_date(w_start) if w_start == w_end else f"{short_date(w_start)}–{w_end.day}"
        total = sum(
            r["total_price"] for r in receipts
            if w_start.isoformat() <= r["purchase_date"] <= w_end.isoformat()
        )
        weeks.append({
            "Week": label, "order": len(weeks), "Spent": round(total, 2),
            "Status": "Over budget" if total > weekly_budget else "Within budget",
            "Current": "This week" if w_start <= today <= w_end else "",
        })
        monday += timedelta(days=7)
    weekly_df = pd.DataFrame(weeks)
    week_order = list(weekly_df["Week"])

    columns = alt.Chart(weekly_df).mark_bar(cornerRadiusEnd=6).encode(
        x=alt.X("Week:N", sort=week_order, title=None, axis=alt.Axis(labelAngle=0, labelLimit=90)),
        y=alt.Y("Spent:Q", title="Spent (CAD)", axis=alt.Axis(format="$,.0f", tickMinStep=1)),
        color=alt.Color(
            "Status:N", title=None,
            scale=alt.Scale(domain=["Within budget", "Over budget"], range=[GREEN, RED]),
            legend=alt.Legend(orient="bottom"),
        ),
        tooltip=[
            alt.Tooltip("Week:N"), alt.Tooltip("Spent:Q", format="$,.2f"),
            alt.Tooltip("Status:N"), alt.Tooltip("Current:N", title=" "),
        ],
    )
    budget_line = alt.Chart(pd.DataFrame({"Budget": [weekly_budget]})).mark_rule(
        color="#111310", strokeDash=[6, 4], size=2
    ).encode(y="Budget:Q", tooltip=[alt.Tooltip("Budget:Q", title="Weekly budget", format="$,.2f")])
    budget_label = alt.Chart(
        pd.DataFrame({"Budget": [weekly_budget], "label": [f"Weekly budget {money(weekly_budget)}"]})
    ).mark_text(align="left", baseline="bottom", dx=4, dy=-4, color="#111310").encode(
        y="Budget:Q", x=alt.value(0), text="label:N"
    )
    chart = (columns + budget_line + budget_label).properties(height=300).configure_view(stroke=None)
    st.altair_chart(chart, width="stretch")
    st.caption(
        "Weeks run Monday to Sunday and are cut at the month's edges. "
        "Uses receipt totals; the dashed line is your weekly budget."
    )
