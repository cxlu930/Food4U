import base64
from html import escape
from pathlib import Path

import streamlit as st

from data.ingredients import SPICE_LEVELS
from db import get_preferences, get_spending_summary, init_db
from services.recommender import get_recommendations

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
.f4u .settings { display:flex; gap:7px; align-items:center; font-size:13px; opacity:.7; }
.f4u .settings .icon { width:20px; height:20px; }
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
.f4u .spark { width:150px; height:65px; color:#bedf39; }
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
.f4u .preferences { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; margin-top:20px; }
.f4u .preference { border:1px solid #dedbd3; border-radius:21px; display:flex; align-items:center; gap:20px; min-height:96px; padding:17px 23px; }
.f4u .preference .preference-copy { min-width:0; flex:1; }
.f4u .preference h2 { font-size:23px; white-space:nowrap; }
.f4u .preference p { font-size:16px; line-height:1.25; margin:6px 0 0; overflow-wrap:anywhere; }
.f4u .preference > .icon:last-child { width:27px; height:27px; }
.f4u .recommendation-heading { display:flex; align-items:center; justify-content:space-between; min-height:70px; margin-top:28px; padding:14px 0 8px; }
.f4u .recommendation-heading h2 { font-size:36px; letter-spacing:-1px; }
.f4u .recommendation-heading img { width:260px; height:200px; object-fit:contain; transform:rotate(-7deg); }
.st-key-recommendation_details { border-top:1px solid #dedbd3; padding-top:15px; }
@media(min-width:1100px) { .f4u .feature { height:290px; } }
@media(max-width:1100px) {
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
 .f4u .stat h2 { font-size:17px; } .f4u .amount { font-size:32px; } .f4u .spark { display:none; }
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

</style>
""", unsafe_allow_html=True)

init_db()
prefs = get_preferences() or {}
summary = get_spending_summary()
spent = summary["spent"]
budget = float(prefs["weekly_budget"])
remaining = round(budget - spent, 2)
spice = prefs.get("spice_level")
if spice is None:
    spice = 0

# Decorative motifs match the reference; they do not represent spending history.
bars = '<svg class="spark" viewBox="0 0 150 65" aria-hidden="true"><path d="M0 64h150" stroke="currentColor"/><g fill="currentColor"><rect x="10" y="48" width="14" height="16" rx="3"/><rect x="39" y="35" width="14" height="29" rx="3"/><rect x="68" y="28" width="14" height="36" rx="3"/><rect x="97" y="17" width="14" height="47" rx="3"/><rect x="126" y="0" width="14" height="64" rx="3"/></g></svg>'
line = '<svg class="spark" viewBox="0 0 150 65" aria-hidden="true"><path d="M2 60Q24 33 47 40T88 31T126 25L146 12V65H2Z" fill="#ddef9b" opacity=".4"/><path d="M2 60Q24 33 47 40T88 31T126 25T146 12" fill="none" stroke="currentColor" stroke-width="4"/><circle cx="146" cy="12" r="6" fill="currentColor"/></svg>'

bars = svg_image(bars.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ').replace('currentColor', '#bedf39'), "spark")
line = svg_image(line.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ').replace('currentColor', '#bedf39'), "spark")

preference_cards = ""
for title, value, glyph in [
    ("Cuisines", labels(prefs.get("cuisines")), "cuisine"),
    ("Spice Level", SPICE_LEVELS.get(spice, "Not specified").title(), "spice"),
    ("Flavors", labels(prefs.get("flavor")), "heart"),
    ("Allergies", labels(prefs.get("avoid_tags")), "allergy"),
]:
    preference_cards += f'<a class="preference" href="./Preferences" target="_self" aria-label="Edit {title}">{icon(glyph)}<div class="preference-copy"><h2>{title}</h2><p>{escape(value)}</p></div>{icon("arrow")}</a>'

st.html(f"""
<div class="f4u">
 <div class="brand-row"><div class="brand">{icon('leaf')}<span>FOOD4U</span></div><a class="settings" href="./Preferences" target="_self" aria-label="Open Preferences">{icon('settings')}Settings</a></div>
 <section class="hero">
  <div><h1>Good food.<br>A little more <span class="underline">ease.</span></h1><p class="intro">Turn your groceries, pantry, and budget<br>into meals you actually want to eat.</p></div>
  <img class="hero-art" src="{artwork('bowl')}" alt="Hand drawn noodle bowl with egg, tomatoes and greens">
 </section>
 <section class="stats" aria-label="Weekly spending overview">
  <div class="stat"><div><h2>Daily Spending</h2><div class="amount">${spent:,.2f}</div><div class="stat-note">Spent this week · Chart illustrative only</div></div><span title="Decorative illustration, not spending data">{bars}</span></div>
  <div class="stat"><div><h2>Remaining Budget</h2><div class="amount">${remaining:,.2f}</div><div class="stat-note">Weekly budget: ${budget:,.2f}</div></div><span title="Decorative illustration, not spending data">{line}</span></div>
 </section>
 <section class="features" aria-label="Your kitchen">
  <a class="feature receipt" href="./Receipt" target="_self" aria-label="Upload Receipt: open receipt upload page">
   <div class="feature-copy"><h2>Upload<br>Receipt</h2><p>Bring your groceries into your kitchen inventory.</p><div class="upload-target">{icon('upload')}<span>Upload a receipt<br>Click to get started</span></div></div>
   <img src="{artwork('receipt')}" alt="Grocery receipt beside a shopping bag of vegetables">
  </a>
  <a class="feature pantry" href="./Pantry" target="_self" aria-label="Open My Pantry">
   <div class="feature-copy"><h2>My Pantry</h2><p>See and manage<br>what’s in your kitchen.</p><span class="round-arrow">{icon('arrow')}</span></div>
   <img src="{artwork('pantry')}" alt="Two pantry jars with lime green lids">
  </a>
 </section>
 <nav class="preferences" aria-label="Food preferences">{preference_cards}</nav>
 <section class="recommendation-heading"><h2>This Week’s Recommendation</h2></section>
</div>
""")

if remaining < 0:
    st.warning("You have exceeded your weekly budget.")

with st.container(key="recommendation_details"):
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
          <a class="recipe-open" href="./Recipes" target="_self">View recipe {icon('arrow')}</a></div>
          {f'<ul class="recipe-reasons">{reasons}</ul>' if reasons else ''}
          {warnings}<p class="recipe-shopping">{escape(shopping)}</p>
        </article></div>
        """)
    else:
        st.info("No recipe suggestions yet. Add pantry items or review your dietary preferences to find your next meal.")
    if not results:
        st.page_link("pages/2_Recipes.py", label="Recipe Recommendation →")
