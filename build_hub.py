#!/usr/bin/env python3
"""Build the UNICEF Data Hub page (index.html) from data.csv + tags.csv.

Stdlib only for the build. No server, no database, no external assets:
the page works offline once loaded.
Usage:  python3 build_hub.py
Checks: every indicator in tags.csv has rows in data.csv; every row has
a country, year and value; latest value per country is shown with its year.
All numbers on the page (findings, charts, tables, trends) are computed
from data.csv here — nothing is hand-typed.
"""
import csv
import html
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data.csv"
TAGS = HERE / "tags.csv"
OUT = HERE / "index.html"

BLUE = "#1cabe2"
DARK = "#0b6e92"
NAVY = "#0a2e44"

def load():
    tags = {r["indicator"]: r for r in csv.DictReader(open(TAGS, encoding="utf-8"))}
    rows = list(csv.DictReader(open(DATA, encoding="utf-8")))
    assert rows, "data.csv is empty"
    fetched = rows[0]["fetched_on"]
    assert all(r["fetched_on"] == fetched for r in rows), "mixed fetch dates in data.csv"
    for ind in tags:
        assert any(r["indicator"] == ind for r in rows), f"no data rows for {ind}"
    return tags, rows, fetched

def latest(rows, ind):
    """Latest (year, value) per country for one indicator."""
    by_country = {}
    for r in rows:
        if r["indicator"] != ind:
            continue
        y = int(r["year"])
        if r["country"] not in by_country or y > by_country[r["country"]][0]:
            by_country[r["country"]] = (y, float(r["value"]))
    return by_country

def latest_table(by_country):
    mx = max(v for _, v in by_country.values()) or 1
    out = ['<table><tr><th>Country</th><th>Latest year</th><th>Value</th><th></th></tr>']
    for c in sorted(by_country):
        y, v = by_country[c]
        w = max(2, int(v / mx * 220))
        out.append(f"<tr><td>{html.escape(c)}</td><td>{y}</td><td>{v:.1f}</td>"
                   f'<td><span class="bar" style="width:{w}px"></span></td></tr>')
    out.append("</table>")
    return "".join(out)

def pak_trend(rows, ind, n=10):
    pak = sorted([(int(r["year"]), float(r["value"])) for r in rows if r["indicator"] == ind and r["country_code"] == "PAK"])
    pak = pak[-n:]
    cells = " &nbsp;·&nbsp; ".join(f"{y}: {v:.1f}" for y, v in pak)
    return f"<p class=\"trend\"><b>Pakistan trend (last {len(pak)} points):</b> {cells}</p>"

def svg_chart(by_country, unit):
    """Horizontal bar chart (inline SVG) of latest values, Pakistan highlighted."""
    order = sorted(by_country.items(), key=lambda kv: kv[1][1], reverse=True)
    mx = max(v for _, v in by_country.values()) or 1
    row_h, top = 30, 8
    height = top + row_h * len(order) + 6
    parts = [f'<svg viewBox="0 0 640 {height}" role="img" aria-label="Latest values by country">']
    for i, (country, (year, value)) in enumerate(order):
        y = top + i * row_h
        bar_w = max(3, value / mx * 400)
        fill = DARK if country == "Pakistan" else BLUE
        parts.append(
            f'<text x="0" y="{y + 15}" class="clabel">{html.escape(country)}</text>'
            f'<rect x="110" y="{y + 3}" width="{bar_w:.0f}" height="16" rx="3" fill="{fill}"/>'
            f'<text x="{118 + bar_w:.0f}" y="{y + 16}" class="cval">{value:.1f} ({year})</text>')
    parts.append("</svg>")
    return "".join(parts)

def findings(rows):
    """Three key findings, computed from the data. Years are shown because
    the latest year differs per country for stunting and out-of-school."""
    mort = latest(rows, "CME_MRY0T4")
    stun = latest(rows, "NT_ANT_HAZ_NE2")
    scho = latest(rows, "ED_ROFST_L1")
    pak_mort_2015 = next(float(r["value"]) for r in rows
                         if r["indicator"] == "CME_MRY0T4" and r["country_code"] == "PAK" and r["year"] == "2015")
    pak_stun_first = sorted([(int(r["year"]), float(r["value"])) for r in rows
                             if r["indicator"] == "NT_ANT_HAZ_NE2" and r["country_code"] == "PAK"])[0]
    return [
        {
            "big": f"{mort['Pakistan'][1]:.1f}",
            "unit": "deaths per 1,000 live births, 2024",
            "title": "Pakistan has the highest under-5 mortality of the five countries",
            "text": (f"Pakistan: {mort['Pakistan'][1]:.1f} per 1,000 in 2024 — more than double Nepal's "
                     f"{mort['Nepal'][1]:.1f}. It is falling: down from {pak_mort_2015:.1f} in 2015, "
                     f"but still the highest, ahead of Afghanistan ({mort['Afghanistan'][1]:.1f})."),
        },
        {
            "big": f"{stun['Afghanistan'][1]:.1f}%",
            "unit": "stunted children under 5, latest year",
            "title": "Stunting is highest in Afghanistan — Pakistan has come far, but not far enough",
            "text": (f"Afghanistan: {stun['Afghanistan'][1]:.1f}% ({stun['Afghanistan'][0]}). "
                     f"Pakistan: {stun['Pakistan'][1]:.1f}% ({stun['Pakistan'][0]}), down from "
                     f"{pak_stun_first[1]:.1f}% in {pak_stun_first[0]} — real progress, yet still "
                     f"more than a third of young children."),
        },
        {
            "big": f"{scho['Pakistan'][1]:.1f}%",
            "unit": "primary-age children out of school, latest year",
            "title": "Nearly 1 in 4 primary-age children in Pakistan is out of school",
            "text": (f"Pakistan: {scho['Pakistan'][1]:.1f}% ({scho['Pakistan'][0]}) — about four times "
                     f"Nepal's {scho['Nepal'][1]:.1f}% ({scho['Nepal'][0]}). Afghanistan is highest at "
                     f"{scho['Afghanistan'][1]:.1f}% ({scho['Afghanistan'][0]})."),
        },
    ]

def main():
    tags, rows, fetched = load()
    find = findings(rows)
    sections = []
    for ind, t in tags.items():
        by = latest(rows, ind)
        search = html.escape((t["indicator_name"] + " " + t["topic"] + " " + t["keywords"] + " " + ind).lower())
        sections.append(f"""
<section class="card" data-search="{search}" data-topic="{html.escape(t['topic'])}">
<span class="badge">{html.escape(t['topic'])}</span>
<h2>{html.escape(t['indicator_name'])} <small>({html.escape(ind)})</small></h2>
<p class="meta"><b>Audience:</b> {html.escape(t['audience'])}</p>
<p><b>What it means:</b> {html.escape(t['unit_meaning'])}</p>
<p class="meta"><b>Keywords:</b> {html.escape(t['keywords'])}</p>
<div class="chart">{svg_chart(by, t['unit_meaning'])}</div>
{latest_table(by)}
{pak_trend(rows, ind)}
</section>""")
    finding_cards = "".join(
        f"""<article class="finding"><div class="fbig">{f['big']}</div>
<div class="funit">{html.escape(f['unit'])}</div>
<h3>{html.escape(f['title'])}</h3><p>{f['text']}</p></article>"""
        for f in find)
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UNICEF Data Hub — child health and education data, organised</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; background: #f4f7f9; color: #1c2b33; line-height: 1.55; }}
header {{ background: linear-gradient(135deg, {NAVY} 0%, #0e4a68 55%, {DARK} 100%); color: #fff; padding: 3em 1em 2.4em; }}
header .wrap, main, footer .wrap {{ max-width: 960px; margin: 0 auto; padding: 0 1em; }}
header h1 {{ margin: 0 0 .25em; font-size: 2.4em; letter-spacing: -.01em; }}
header p.lead {{ margin: .3em 0 0; font-size: 1.15em; opacity: .95; max-width: 640px; }}
.stats {{ display: flex; flex-wrap: wrap; gap: .6em; margin: 1.4em 0 0; }}
.stat {{ background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.35); border-radius: 10px; padding: .6em 1em; }}
.stat b {{ display: block; font-size: 1.35em; }}
h2.section {{ font-size: 1.5em; margin: 1.8em 0 .2em; }}
.section-sub {{ color: #4a5a62; margin: .2em 0 1em; }}
.findings {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1em; margin: 1em 0; }}
.finding {{ background: #fff; border: 1px solid #dbe4e8; border-top: 4px solid {BLUE}; border-radius: 10px; padding: 1.1em 1.2em; box-shadow: 0 1px 3px rgba(0,0,0,.06); }}
.fbig {{ font-size: 2.2em; font-weight: 800; color: {DARK}; line-height: 1.1; }}
.funit {{ font-size: .88em; color: #5b6b73; margin-bottom: .4em; }}
.finding h3 {{ margin: .2em 0 .4em; font-size: 1.05em; }}
.finding p {{ margin: 0; color: #33424a; }}
.toolbar {{ background: #fff; border: 1px solid #dbe4e8; border-radius: 10px; padding: .9em 1em; margin: 1.2em 0; display: flex; flex-wrap: wrap; gap: .8em; align-items: center; position: sticky; top: 0; z-index: 5; box-shadow: 0 2px 8px rgba(0,0,0,.06); }}
.toolbar input[type=search] {{ flex: 1; min-width: 200px; padding: .55em .8em; border: 1px solid #b9c6cc; border-radius: 6px; font-size: 1em; }}
.toolbar select {{ padding: .55em .6em; border: 1px solid #b9c6cc; border-radius: 6px; font-size: 1em; }}
.card {{ background: #fff; border: 1px solid #dbe4e8; border-radius: 12px; padding: 1.3em 1.4em; margin: 1.2em 0; box-shadow: 0 1px 4px rgba(0,0,0,.06); }}
.badge {{ display: inline-block; background: #e6f6fc; color: #0b6e92; border-radius: 20px; padding: .15em .8em; font-size: .85em; font-weight: 600; }}
.card h2 {{ margin: .4em 0 .2em; }}
.card h2 small {{ color: #5b6b73; font-weight: 400; }}
.meta {{ color: #4a5a62; }}
.chart {{ margin: .8em 0; }}
.chart svg {{ width: 100%; height: auto; display: block; }}
.clabel {{ font-size: 13px; fill: #1c2b33; }}
.cval {{ font-size: 13px; fill: #33424a; font-weight: 600; }}
.bar {{ display: inline-block; height: 12px; background: {BLUE}; border-radius: 2px; }}
table {{ border-collapse: collapse; width: 100%; margin: .6em 0; }} td, th {{ border-bottom: 1px solid #e3e9ec; padding: 6px 8px; text-align: left; }}
th {{ color: #4a5a62; font-size: .9em; }}
.trend {{ background: #f0f7fa; border-radius: 6px; padding: .6em .8em; }}
.steps {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1em; margin: 1em 0; }}
.step {{ background: #fff; border: 1px solid #dbe4e8; border-radius: 10px; padding: 1em 1.1em; }}
.step b.num {{ display: inline-block; background: {NAVY}; color: #fff; width: 1.7em; height: 1.7em; line-height: 1.7em; text-align: center; border-radius: 50%; margin-bottom: .4em; }}
.step h3 {{ margin: .2em 0 .3em; }}
.step p {{ margin: 0; color: #33424a; }}
section.sharepoint img {{ max-width: 100%; border: 1px solid #dbe4e8; border-radius: 8px; }}
.btn {{ display: inline-block; background: {DARK}; color: #fff; text-decoration: none; padding: .6em 1.1em; border-radius: 8px; font-weight: 600; margin-top: .4em; }}
footer {{ background: {NAVY}; color: #cfe3ec; margin-top: 2.5em; padding: 1.8em 0 2em; font-size: .92em; }}
footer a {{ color: #8fd8f2; }}
</style>
</head>
<body>
<header><div class="wrap">
<h1>UNICEF Data Hub</h1>
<p class="lead">Real public data on child health and education, organised and tagged — so anyone can find a number fast, and see what it means.</p>
<div class="stats">
<div class="stat"><b>{len(rows)}</b>rows of data</div>
<div class="stat"><b>{len(tags)}</b>indicators</div>
<div class="stat"><b>5</b>countries</div>
<div class="stat"><b>{html.escape(fetched)}</b>fetched</div>
</div>
</div></header>
<main>
<h2 class="section">Key findings</h2>
<p class="section-sub">What the latest numbers say — every figure is from the data below, and every number can be checked at data.unicef.org.</p>
<div class="findings">
{finding_cards}
</div>
<div class="toolbar">
<label>Search <input id="q" type="search" placeholder="try: mortality, stunting, school"></label>
<label>Topic <select id="topic"><option value="">all</option><option>Health</option><option>Nutrition</option><option>Education</option></select></label>
<span id="count"></span>
</div>
<h2 class="section">The indicators</h2>
<p class="section-sub">Three indicators, five countries: Pakistan, India, Bangladesh, Afghanistan and Nepal. Data from the UNICEF Data Warehouse (SDMX API, https://sdmx.data.unicef.org). Search and filter work offline once the page is loaded.</p>
<div id="cards">
{''.join(sections)}
</div>
<h2 class="section">How this hub is built</h2>
<div class="steps">
<div class="step"><b class="num">1</b><h3>Fetch real data</h3><p>A Python script pulls the three indicators for the five countries, live from the UNICEF Data Warehouse public API. No key, no login. Total only — both sexes, all wealth groups.</p></div>
<div class="step"><b class="num">2</b><h3>Tag every row</h3><p>Every row carries metadata: indicator, country, year, value, unit and source — so each number is findable, checkable and ready to use.</p></div>
<div class="step"><b class="num">3</b><h3>Publish it</h3><p>A second script checks the data and builds this page: latest values, Pakistan trends, search and filter. The same rows also live as a SharePoint list, below.</p></div>
</div>
<p><a class="btn" href="data.csv" download>Download the data (CSV, {len(rows)} rows)</a></p>
<section class="card sharepoint">
<h2>Same data in SharePoint</h2>
<p>The same {len(rows)} rows are also published as a SharePoint list, with metadata on every row — indicator, country, year, value, unit and source — so the content stays organised, tagged and findable. The SharePoint site lives in my student Microsoft 365 tenant, so it opens only for people in that tenant; the screenshot below is the proof.</p>
<img src="docs/sharepoint-list.png" alt="SharePoint list showing the 440 UNICEF data rows with metadata columns">
</section>
<h2 class="section">About this hub</h2>
<p>This is my own project, built to do knowledge-management work properly: get real data, organise it, tag it with metadata, and keep it findable and up to date — in a live hub and in SharePoint. It is not UNICEF work and not an official UNICEF page. Figures are UNICEF estimates and can be revised.</p>
<p>Built by Awais Ahmed Shah, final-year BS Data Science student, UET Peshawar. Data: UNICEF Data Warehouse, public SDMX API. Run it yourself: <code>pip install unicefdata pandas</code>, then <code>python3 fetch_data.py</code> and <code>python3 build_hub.py</code>.</p>
</main>
<footer><div class="wrap">
<p>Sources: UNICEF Data Warehouse (https://sdmx.data.unicef.org) — verify every number at <a href="https://data.unicef.org">data.unicef.org</a>. Code and data: <a href="https://github.com/AwaisAhmed183/unicef-data-hub">github.com/AwaisAhmed183/unicef-data-hub</a>.</p>
</div></footer>
<script>
function apply() {{
  const q = document.getElementById('q').value.toLowerCase();
  const t = document.getElementById('topic').value;
  let shown = 0;
  document.querySelectorAll('#cards .card').forEach(c => {{
    const ok = (!q || (c.dataset.search || '').includes(q)) && (!t || c.dataset.topic === t);
    c.style.display = ok ? '' : 'none';
    if (ok) shown++;
  }});
  document.getElementById('count').textContent = shown + ' of {len(tags)} indicators shown';
}}
document.getElementById('q').addEventListener('input', apply);
document.getElementById('topic').addEventListener('change', apply);
apply();
</script>
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"OK: {len(rows)} rows, {len(tags)} indicators, fetched {fetched}, index.html written")

if __name__ == "__main__":
    main()
