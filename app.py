import base64
from html import escape
from pathlib import Path
from urllib.parse import quote

import streamlit as st

from data.ingredients import SPICE_LEVELS
from db import current_user, get_preferences, get_budget_summary, init_db, save_preferences, sign_out
from services.recommender import get_recommendations, load_recipes

st.set_page_config(page_title="Food4U", page_icon="🌿", layout="wide")

ASSETS = Path(__file__).parent / "assets" / "dashboard"


def artwork(name):
    return "data:image/png;base64," + base64.b64encode((ASSETS / f"{name}.png").read_bytes()).decode()


def labels(values):
    if isinstance(values, str):
        values = [v for v in values.split(",") if v]
    return ", ".join(v.replace("_", " ").title() for v in (values or [])) or "None specified"


def svg_image(svg, css_class="icon"):
    encoded = base64.b64encode(svg.encode()).decode()
    return f'<img class="{css_class}" src="data:image/svg+xml;base64,{encoded}" alt="" aria-hidden="true">'


def icon(name):
    paths = {
        "leaf": '<path d="M7 30C-2 12 13 5 34 3c0 19-6 31-22 27" fill="#bade39" stroke="none"/><path d="M3 36 27 12" stroke="#bade39"/><path d="m10 28 15-15" stroke="#fffaf2"/>',
        "cuisine": '<path d="M8 5v13m6-13v13M2 5v11c0 8 18 8 18 0V5M11 22v18M33 5c-9 5-8 19 0 19h4V5h-4v35"/>',
        "spice": '<path d="M30 13c-3-4-9-1-10 5C17 29 7 31 2 30c10 14 30 7 34-8 2-7-1-11-6-9Zm0 0c0-6 3-7 6-8"/>',
        "heart": '<path d="M21 37 5 22C-8 6 12-2 21 10 30-2 50 6 37 22Z"/>',
        "allergy": '<circle cx="21" cy="21" r="18"/><path d="m8 8 26 26m0-26L8 34"/>',
        "arrow": '<path d="M7 21h27m-10-10 11 10-11 10"/>',
        "upload": '<path d="M21 29V5M11 15 21 5l10 10M5 27v12h32V27"/>',
        "budget": '<rect x="4" y="10" width="36" height="27" rx="5"/><path d="M9 10V6h25v4M28 19h12v10H28a5 5 0 0 1 0-10Z"/><circle cx="31" cy="24" r="1"/>',
        "settings": '<circle cx="21" cy="21" r="7"/><path d="m17 3 8 0 1 6 5 3 6-2 4 7-5 4v5l5 4-4 7-6-2-5 3-1 5h-8l-1-5-5-3-6 2-4-7 5-4v-5l-5-4 4-7 6 2 5-3Z"/>',
    }
    return svg_image(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 44" fill="none" stroke="#111310" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">{paths[name]}</svg>')


st.markdown("""
<style>
.stApp { background: #fdf9f2; color: #111310; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"] { display: none; }
[data-testid="stMainBlockContainer"] { max-width: 1440px; padding: 20px 36px 55px; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap: 0; }
.f4u, .f4u * { box-sizing: border-box; }
.f4u { font-family: Arial, Helvetica, sans-serif; color: #111310; }
.f4u a { color: inherit; text-decoration: none; }
.f4u a:focus-visible { outline: 3px solid #6a8e15; outline-offset: 5px; }
.f4u a:hover { border-color: #b8d844; }
.f4u .icon { width: 44px; height: 44px; flex-shrink: 0; }
.f4u .brand { display:flex; align-items:center; gap:10px; font-size:25px; font-weight:800; }
.f4u .brand .icon { width:39px; height:39px; }
.f4u .brand-row { display:flex; justify-content:space-between; align-items:center; }
[data-testid="stMainBlockContainer"] { position: relative; }
.st-key-settings_menu { position:absolute; top:24px; right:36px; width:auto; z-index:20; }
.st-key-settings_menu button { background:transparent; border:0; box-shadow:none; color:#111310; font-size:13px; opacity:.7; padding:4px 8px; min-height:0; }
.st-key-settings_menu button:hover { opacity:1; background:#efeadd; }
.f4u .hero { display:grid; grid-template-columns: 1.45fr 1fr; align-items:center; min-height:270px; gap:30px; }
.f4u h1 { font-family:Arial,Helvetica,sans-serif !important; color:#111310; font-weight:800 !important; font-size:clamp(42px,4.7vw,70px) !important; line-height:1.01 !important; letter-spacing:-2.5px; margin:12px 0 14px; padding:0; }
.f4u h1 .underline { position:relative; white-space:nowrap; }
.f4u h1 .underline::after { content:""; position:absolute; width:125px; height:8px; border-radius:8px; background:#bedf39; bottom:-10px; right:0; transform:rotate(-10deg); }
.f4u .intro { font-size:21px; line-height:1.35; margin:18px 0 25px; }
.f4u .hero-art { width:100%; height:270px; object-fit:contain; }
.f4u .stats { display:grid; grid-template-columns:1fr 1fr; gap:22px; margin:8px 0 24px; }
.f4u .stat { border:1px solid #dedbd3; border-radius:21px; padding:12px 34px; min-height:110px; display:flex; align-items:center; justify-content:space-between; gap:15px; }
.f4u h2 { font-family:Arial,Helvetica,sans-serif !important; font-weight:800; color:inherit; margin:0; padding:0; font-size:23px; letter-spacing:-.7px; line-height:1.1; }
.f4u .amount { font-size:43px; font-weight:750; letter-spacing:-1px; line-height:1.15; margin-top:10px; }
.f4u .stat-note { font-size:11px; color:#657044; margin-top:3px; }
.f4u .stat > div { width: 100%; min-width: 0; }
.f4u .stat-note { line-height: 1.35; }
.f4u .daily-empty { color: #7b806a; font-size: 11px; margin-top: 6px; }
.f4u .remaining-card { position: relative; cursor: pointer; transition: border-color .15s, box-shadow .15s; }
.f4u .remaining-card:hover { border-color: #B8E33D; box-shadow: 0 3px 12px #526b2e12; }
.f4u .remaining-card .stat-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.f4u .remaining-card .stat-heading .icon { width: 22px; height: 22px; }
.f4u .remaining-card.is-over-budget { border-color: #c79846; }
.f4u .remaining-card.is-over-budget:hover { border-color: #B8E33D; }
.f4u .budget-warning { color: #805313; font-size: 11px; margin-top: 5px; }
.f4u .budget-usage { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.f4u .budget-track { height: 6px; border-radius: 999px; background: #e7e9db; overflow: hidden; margin-top: 8px; }
.f4u .budget-fill { height: 100%; border-radius: inherit; background: #B8E33D; }
.f4u .features { display:grid; grid-template-columns:1.45fr 1fr; gap:28px; }
.f4u .feature { border:1px solid #dedbd3; border-radius:30px; position:relative; overflow:hidden; min-height:290px; padding:26px 32px; display:flex; align-items:center; }
.f4u .receipt { background:radial-gradient(ellipse at 65% 55%,#f0f5bb,#f5f7d2); border-color:transparent; }
.f4u .feature-copy { width:48%; position:relative; z-index:1; }
.f4u .receipt h2 { font-size:52px; line-height:1.01; letter-spacing:-1.5px; }
.f4u .pantry h2 { font-size:42px; white-space:nowrap; }
.f4u .feature p { font-size:19px; line-height:1.25; margin:12px 0 22px; }
.f4u .feature > img { position:absolute; right:0; top:5%; width:54%; height:92%; object-fit:contain; }
.f4u .receipt > img { width:55%; }
.f4u .upload-target { display:flex; align-items:center; gap:16px; padding:10px 15px; border:2px dashed #303521; border-radius:14px; width:100%; font-size:16px; line-height:1.3; }
.f4u .round-arrow { display:flex; align-items:center; justify-content:center; background:#c9e55b; border-radius:999px; width:64px; height:48px; margin-top:56px; }
.f4u .round-arrow .icon { width:34px; height:34px; }
.f4u .preferences { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:16px; margin-top:20px; }
.f4u .preference { border:1px solid #dedbd3; border-radius:21px; display:flex; align-items:center; gap:10px; height:112px; min-height:112px; padding:16px; }
.f4u .preference .preference-copy { min-width:0; flex:1; }
.f4u .preference h2 { font-size:clamp(17px,1.4vw,20px); white-space:normal; line-height:1.1; }
.f4u .preference p { font-size:14px; line-height:1.25; margin:6px 0 0; overflow-wrap:anywhere; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.f4u .preference > .icon:first-child { width:32px; height:32px; }
.f4u .preference > .icon:last-child { width:20px; height:20px; }
.f4u .recommendation-heading { display:flex; align-items:center; justify-content:space-between; min-height:70px; margin-top:28px; padding:14px 0 8px; }
.f4u .recommendation-heading h2 { font-size:36px; letter-spacing:-1px; }
.f4u .recommendation-heading img { width:260px; height:200px; object-fit:contain; transform:rotate(-7deg); }
.st-key-home_recommendation_row { margin-top:28px; }
.st-key-home_recommendation_row [data-testid="stHorizontalBlock"]:has(.st-key-recommendation_details) {
 display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); align-items:stretch;
}
.st-key-home_recommendation_row [data-testid="stHorizontalBlock"]:has(.st-key-recommendation_details) > [data-testid="stColumn"] { width:100%; min-width:0; }
.st-key-recommendation_details, .st-key-explore_recipes {
 border:1px solid #d6ddbf !important; border-radius:26px !important;
 background:#edf3d6; padding:24px !important; height:100%; min-width:0;
}
.st-key-home_recommendation_row h3 { font-family:Arial,Helvetica,sans-serif !important; color:#111310; font-size:27px; font-weight:800; letter-spacing:-.7px; }
.st-key-home_recommendation_row .st-key-recommendation_details .recipe-result { border:0; padding:0; background:transparent; margin-top:6px; }
.st-key-home_recommendation_row .st-key-recommendation_details .recipe-top { justify-content:flex-start; flex-wrap:wrap; gap:8px 14px; }
.st-key-home_recommendation_row .st-key-recommendation_details .recipe-result h2 { font-size:25px; }
.st-key-home_recommendation_row .st-key-recommendation_details .recipe-reasons li { max-width:100%; white-space:normal; overflow-wrap:anywhere; }
.st-key-explore_recipes [data-testid="stHtml"] { height:100%; }
.st-key-explore_recipes .explore-content { display:flex; flex-direction:column; gap:18px; height:100%; }
.st-key-explore_recipes .explore-content h2 { font-size:27px; letter-spacing:-.7px; }
.st-key-explore_recipes .explore-art { font-size:76px; line-height:1.2; text-align:center; padding:8px; letter-spacing:10px; }
.st-key-explore_recipes .explore-copy { margin:0; color:#52623a; font-size:16px; line-height:1.55; }
.st-key-explore_recipes .explore-facts { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.st-key-explore_recipes .explore-fact { border:1px solid #d6ddbf; border-radius:16px; background:#FDF9F2; padding:16px; }
.st-key-explore_recipes .explore-fact strong { display:block; font-size:32px; color:#111310; }
.st-key-explore_recipes .explore-fact span { font-size:13px; color:#657044; }
.st-key-explore_recipes .explore-action { display:block; text-align:center; border-radius:999px; padding:14px 20px; background:#B8E33D; color:#111310; font-weight:800; margin-top:auto; }
.st-key-explore_recipes .explore-action:hover { background:#a9d330; }
@media(max-width:760px) {
 .st-key-home_recommendation_row [data-testid="stHorizontalBlock"]:has(.st-key-recommendation_details) { grid-template-columns:minmax(0,1fr); }
 .st-key-recommendation_details, .st-key-explore_recipes { padding:18px !important; }
 .st-key-explore_recipes .explore-art { font-size:58px; }
}
@media(min-width:1100px) { .f4u .feature { height:290px; } }
@media(max-width:1100px) {
 .f4u .preferences { grid-template-columns:repeat(2,minmax(0,1fr)); }
 .f4u .receipt h2 { font-size:40px; } .f4u .pantry h2 { font-size:34px; }
 .f4u .feature { padding:22px; } .f4u .feature p { font-size:16px; }
 .f4u .preference { padding:15px; gap:10px; } .f4u .preference h2 { font-size:20px; }
 .f4u .preference > .icon:first-child { width:32px; }
}
@media(max-width:760px) {
 [data-testid="stMainBlockContainer"] { padding:18px; }
 .f4u .hero { grid-template-columns:1fr; gap:0; } .f4u .hero-art { height:180px; grid-row:2; }
 .f4u h1 { letter-spacing:-1.5px; } .f4u .intro { font-size:17px; }
 .f4u .stats { gap:12px; } .f4u .stat { padding:16px; min-height:110px; }
 .f4u .stat h2 { font-size:17px; } .f4u .amount { font-size:32px; }
 .f4u .features { grid-template-columns:1fr; gap:16px; }
 .f4u .preferences { grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
 .f4u .preference h2 { white-space:normal; } .f4u .preference > .icon:last-child { display:none; }
 .f4u .recommendation-heading h2 { font-size:27px; } .f4u .recommendation-heading img { width:130px; }
}

.f4u .recipe-result { border:1px solid #dedbd3; border-radius:24px; background:#f5f5df; padding:26px 30px; margin-top:12px; }
.f4u .recipe-top { display:flex; justify-content:space-between; align-items:center; gap:20px; }
.f4u .eyebrow { display:block; color:#687347; font-size:11px; font-weight:700; letter-spacing:1.5px; margin-bottom:9px; }
.f4u .recipe-result h2 { font-size:29px; }
.f4u .recipe-meta { font-size:15px; color:#5d634d; margin:10px 0; }
.f4u .recipe-open { display:flex; align-items:center; gap:8px; border-radius:30px; background:#c9e55b; padding:10px 18px; white-space:nowrap; font-size:14px; }
.f4u .recipe-open .icon { width:22px; height:22px; }
.f4u .recipe-reasons { display:flex; gap:8px; flex-wrap:wrap; list-style:none; padding:0; margin:18px 0; }
.f4u .recipe-reasons li { background:#e6edc9; border-radius:12px; padding:8px 12px; font-size:13px; color:#405326; }
.f4u .recipe-warning { background:#fff1d9; color:#805313; padding:10px 14px; border-radius:12px; }
.f4u .recipe-shopping { font-size:14px; border-top:1px solid #dce2c6; padding-top:14px; margin:14px 0 0; }
.st-key-recommendation_details [role="radiogroup"] { gap:10px; }
.st-key-recommendation_details [role="radiogroup"] label { border:1px solid #dedbd3; border-radius:22px; padding:7px 13px; background:#fdf9f2; }
.st-key-recommendation_details [role="radiogroup"] label:has(input:checked) { background:#eaf1cb; border-color:#b8d44f; }
@media(max-width:760px) { .f4u .recipe-top { align-items:flex-start; flex-direction:column; } .f4u .recipe-result { padding:20px; } }

.st-key-home_budget_cards { margin:8px 0 24px; }
.st-key-home_budget_cards [data-testid="stHorizontalBlock"]:has(.st-key-home_budget_period_card) {
 display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); align-items:stretch;
}
.st-key-home_budget_cards [data-testid="stHorizontalBlock"]:has(.st-key-home_budget_period_card) > [data-testid="stColumn"] { width:100%; min-width:0; }
.st-key-home_budget_period_card { border:0 !important; padding:0 !important; height:100%; }
.st-key-home_budget_period_card [data-testid="stElementContainer"],
.st-key-home_budget_period_card [data-testid="stButton"] { height:100%; }
.st-key-home_budget_period_card button {
 position:relative; display:flex; flex-direction:column; align-items:flex-start; justify-content:center;
 width:100%; height:100%; min-height:146px; padding:18px 32px; text-align:left;
 border:1px solid #b8cb80; border-radius:21px; background:#D5E69B; color:#111310;
 cursor:pointer; gap:7px; transition:background .15s, border-color .15s, box-shadow .15s;
}
.st-key-home_budget_period_card button::before {
 content:"BUDGET PERIOD"; font:700 11px Arial,Helvetica,sans-serif; letter-spacing:1.3px; color:#52623a;
}
.st-key-home_budget_period_card button [data-testid="stMarkdownContainer"] {
 display:block; width:100%; text-align:left; align-self:stretch;
 justify-content:flex-start; align-items:flex-start;
}
.st-key-home_budget_period_card button p {
 font:800 clamp(32px,3.5vw,44px)/1.12 Arial,Helvetica,sans-serif;
 color:#111310; white-space:nowrap !important; word-break:normal; margin:0; letter-spacing:-1px; text-align:left;
}
.st-key-home_budget_period_card button p::after {
 content:"↻"; position:absolute; top:14px; right:22px; font-size:25px; font-weight:500; color:#52623a;
}
.st-key-home_budget_period_card button::after { content:"Click anywhere to switch"; font:400 11px Arial,Helvetica,sans-serif; color:#657044; }
.st-key-home_budget_period_card button:hover { background:#ccdf89; border-color:#9DBD43; color:#111310; box-shadow:0 3px 12px #526b2e15; }
.st-key-home_budget_period_card button:focus-visible { outline:3px solid #9DBD43; outline-offset:3px; }
.st-key-home_remaining_budget [data-testid="stHtml"], .st-key-home_remaining_budget .f4u { height:100%; }
.st-key-home_remaining_budget .remaining-card { height:100%; box-sizing:border-box; }
@media(max-width:760px) {
 .st-key-home_budget_cards [data-testid="stHorizontalBlock"]:has(.st-key-home_budget_period_card) { grid-template-columns:minmax(0,1fr); }
 .st-key-home_budget_period_card button { padding:18px 32px; }
}
</style>
""", unsafe_allow_html=True)

init_db()
prefs = get_preferences() or {}
nick_q = "?u=" + quote(current_user() or "")  # plain links reload the app, so they carry the nickname
budget_period = prefs["budget_period"]


def toggle_home_budget_period():
    latest_preferences = get_preferences()
    latest_preferences["budget_period"] = "monthly" if latest_preferences["budget_period"] == "weekly" else "weekly"
    save_preferences(latest_preferences)


summary = get_budget_summary(budget_period)
spent = summary["spent"]
budget = float(summary["budget"])
remaining = summary["remaining"]
period_label = budget_period.title()
period_noun = "month" if budget_period == "monthly" else "week"
spice = prefs.get("spice_level")
if spice is None:
    spice = 0

if budget > 0:
    used_percent = spent / budget * 100
    filled_percent = min(max(used_percent, 0.0), 100.0)
    usage_label = f"Budget Used: {used_percent:.1f}% used"
    budget_progress = (
        f'<div class="budget-track" role="progressbar" aria-label="{period_label} budget used" '
        f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{filled_percent:.2f}" '
        f'aria-valuetext="{used_percent:.1f}% of budget used">'
        f'<div class="budget-fill" style="width:{filled_percent:.2f}%"></div></div>'
    )
else:
    usage_label = "Budget Used: — (zero budget)"
    budget_progress = (
        '<div class="budget-track" role="img" '
        'aria-label="Budget usage unavailable: No positive budget allocated"></div>'
    )

budget_warning = (
    f'<div class="budget-warning">Over budget by ${abs(remaining):,.2f}</div>'
    if remaining < 0 else ""
)

preference_cards = ""
for title, value, glyph in [
    ("Budget", f"${budget:,.2f} CAD / {period_noun}", "budget"),
    ("Cuisines", labels(prefs.get("cuisines")), "cuisine"),
    ("Spice Level", SPICE_LEVELS.get(spice, "Not specified").title(), "spice"),
    ("Flavors", labels(prefs.get("flavor")), "heart"),
    ("Allergies", labels(prefs.get("avoid_tags")), "allergy"),
]:
    preference_cards += f'<a class="preference" href="./Preferences{nick_q}" target="_self" aria-label="Edit {title}">{icon(glyph)}<div class="preference-copy"><h2>{title}</h2><p title="{escape(value, quote=True)}">{escape(value)}</p></div>{icon("arrow")}</a>'

with st.container(key="settings_menu"):
    with st.popover("Settings", icon=":material/settings:"):
        st.markdown(f"Signed in as **{current_user()}**")
        if st.button("Switch user", key="switch_user", use_container_width=True):
            sign_out()

st.html(f"""
<div class="f4u">
 <div class="brand-row"><div class="brand">{icon('leaf')}<span>FOOD4U</span></div></div>
 <section class="hero">
  <div><h1>Good food.<br>A little more <span class="underline">ease.</span></h1><p class="intro">Turn your groceries, pantry, and budget<br>into meals you actually want to eat.</p></div>
  <img class="hero-art" src="{artwork('bowl')}" alt="Hand drawn noodle bowl with egg, tomatoes and greens">
 </section>
</div>
""")

with st.container(key="home_budget_cards"):
    period_column, remaining_column = st.columns(2, gap="medium")
    with period_column:
        with st.container(height="stretch", key="home_budget_period_card"):
            st.button(
                period_label, key="toggle_budget_period", width="stretch",
                on_click=toggle_home_budget_period,
            )
    with remaining_column:
        with st.container(height="stretch", key="home_remaining_budget"):
            st.html(f"""
<div class="f4u">
  <a class="stat remaining-card{' is-over-budget' if remaining < 0 else ''}" href="./Preferences{nick_q}" target="_self" aria-label="Remaining Budget: edit budget in Preferences"><div><div class="stat-heading"><h2>Remaining Budget</h2>{icon('arrow')}</div><div class="amount">${remaining:,.2f}</div><div class="stat-note budget-usage"><span>{period_label} budget: ${budget:,.2f}</span><span>{usage_label}</span></div>{budget_progress}{budget_warning}</div></a>
</div>
""")

st.html(f"""
<div class="f4u">
 <section class="features" aria-label="Your kitchen">
  <a class="feature receipt" href="./Receipt{nick_q}" target="_self" aria-label="Upload Receipt: open receipt upload page">
   <div class="feature-copy"><h2>Upload<br>Receipt</h2><p>Bring your groceries into your kitchen inventory.</p><div class="upload-target">{icon('upload')}<span>Upload a receipt<br>Click to get started</span></div></div>
   <img src="{artwork('receipt')}" alt="Grocery receipt beside a shopping bag of vegetables">
  </a>
  <a class="feature pantry" href="./Pantry{nick_q}" target="_self" aria-label="Open My Pantry">
   <div class="feature-copy"><h2>My Pantry</h2><p>See and manage<br>what’s in your kitchen.</p><span class="round-arrow">{icon('arrow')}</span></div>
   <img src="{artwork('pantry')}" alt="Two pantry jars with lime green lids">
  </a>
 </section>
 <nav class="preferences" aria-label="Food preferences">{preference_cards}</nav>
</div>
""")

if remaining < 0:
    st.warning(f"You are ${abs(remaining):,.2f} over your {period_label.lower()} budget.")

with st.container(key="home_recommendation_row"):
    recommendation_column, explore_column = st.columns(2, gap="medium")
    with recommendation_column:
        with st.container(border=True, height="stretch", key="recommendation_details"):
            st.subheader("This Week’s Recommendation")
            st.caption("Recipe recommendations currently use your weekly budget, including when the dashboard is in Monthly view.")
            mode_label = st.radio("Find something delicious", ["Plan my meals", "Cook with what I have"], horizontal=True)
            mode = "plan_my_meals" if mode_label == "Plan my meals" else "cook_with_what_i_have"
            recommendations = None
            try:
                with st.spinner("Finding ideas for your kitchen…"):
                    recommendations = get_recommendations(mode)
            except (OSError, ValueError, KeyError):
                st.info("Recipe ideas are temporarily unavailable. Please try again later.")
            results = recommendations.get("results", []) if recommendations is not None else []
            if results:
                result = results[0]
                recipe = result["recipe"]
                reasons = "".join(f"<li>{escape(reason)}</li>" for reason in result.get("reasons", []))
                warnings = "".join(f'<p class="recipe-warning">{escape(warning)}</p>' for warning in result.get("warnings", []))
                missing = result.get("missing_ingredients", [])
                shopping = "Shopping list: " + labels(missing) if missing else "Your pantry has all the listed ingredients."
                st.html(f"""
                <div class="f4u"><article class="recipe-result">
                  <div class="recipe-top"><div><span class="eyebrow">PICKED FOR YOUR KITCHEN</span>
                  <h2>{escape(recipe['name'])}</h2>
                  <p class="recipe-meta">{escape(labels([recipe['cuisine']]))} · {recipe['time_minutes']} min · Estimated ${recipe['estimated_price']:.2f} per serving</p></div>
                  <a class="recipe-open" href="./Recipes{nick_q}" target="_self">View recipe {icon('arrow')}</a></div>
                  {f'<ul class="recipe-reasons">{reasons}</ul>' if reasons else ''}
                  {warnings}<p class="recipe-shopping">{escape(shopping)}</p>
                </article></div>
                """)
            else:
                st.info("No recipe suggestions yet. Add pantry items or review your dietary preferences to find your next meal.")
            if not results:
                st.page_link("pages/2_Recipes.py", label="Recipe Recommendation →")

    with explore_column:
        with st.container(border=True, height="stretch", key="explore_recipes"):
            try:
                recipe_catalog = load_recipes()
                recipe_count = len(recipe_catalog)
                cuisine_count = len({recipe["cuisine"] for recipe in recipe_catalog if recipe.get("cuisine")})
                catalog_summary = (
                    f'<div class="explore-facts"><div class="explore-fact"><strong>{recipe_count}</strong><span>Recipes to explore</span></div>'
                    f'<div class="explore-fact"><strong>{cuisine_count}</strong><span>Cuisines to discover</span></div></div>'
                )
            except (OSError, ValueError, KeyError, TypeError):
                catalog_summary = '<p class="explore-copy">Recipe counts are temporarily unavailable. You can still open Recipes.</p>'
            st.html(f"""
            <div class="f4u explore-content">
              <h2>Explore Recipes</h2>
              <p class="explore-copy">What are we cooking? Find a new favorite, revisit a familiar comfort, or make the most of what’s already in your pantry.</p>
              <div class="explore-art" role="img" aria-label="A pan, avocado and noodle bowl">🍳🥑🍜</div>
              {catalog_summary}
              <p class="explore-copy">Browse by cuisine, save the dishes you love, and see what you need to buy.</p>
              <a class="explore-action" href="./Recipes{nick_q}" target="_self">Explore all recipes →</a>
            </div>
            """)
