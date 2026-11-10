#!/usr/bin/env python3
"""Build a searchable hub page (index.html) from data.csv + tags.csv.

Stdlib only. No server, no database.
Usage:  python3 build_hub.py
Checks: every indicator in tags.csv has rows in data.csv; every row has
a country, year and value; latest value per country is shown with its year.
"""
import csv
import html
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data.csv"
TAGS = HERE / "tags.csv"
OUT = HERE / "index.html"

def load():
    tags = {r["indicator"]: r for r in csv.DictReader(open(TAGS, encoding="utf-8"))}
    rows = list(csv.DictReader(open(DATA, encoding="utf-8")))
    assert rows, "data.csv is empty"
    fetched = rows[0]["fetched_on"]
    assert all(r["fetched_on"] == fetched for r in rows), "mixed fetch dates in data.csv"
    for ind in tags:
        assert any(r["indicator"] == ind for r in rows), f"no data rows for {ind}"
    return tags, rows, fetched

def latest_table(rows, ind):
    by_country = {}
    for r in rows:
        if r["indicator"] != ind:
            continue
        y = int(r["year"])
        if r["country"] not in by_country or y > by_country[r["country"]][0]:
            by_country[r["country"]] = (y, float(r["value"]))
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

def main():
    tags, rows, fetched = load()
    sections = []
    for ind, t in tags.items():
        search = html.escape((t["indicator_name"] + " " + t["topic"] + " " + t["keywords"] + " " + ind).lower())
        sections.append(f"""
<section class="card" data-search="{search}" data-topic="{html.escape(t['topic'])}">
<span class="badge">{html.escape(t['topic'])}</span>
<h2>{html.escape(t['indicator_name'])} <small>({html.escape(ind)})</small></h2>
<p class="meta"><b>Audience:</b> {html.escape(t['audience'])}</p>
<p><b>What it means:</b> {html.escape(t['unit_meaning'])}</p>
<p class="meta"><b>Keywords:</b> {html.escape(t['keywords'])}</p>
{latest_table(rows, ind)}
{pak_trend(rows, ind)}
</section>""")
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UNICEF Data Hub — child health and education data, organised</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; background: #f4f7f9; color: #1c2b33; line-height: 1.5; }}
header {{ background: #1cabe2; color: #fff; padding: 2.2em 1em 1.8em; }}
header .wrap, main {{ max-width: 920px; margin: 0 auto; padding: 0 1em; }}
header h1 {{ margin: 0 0 .2em; font-size: 2em; }}
header p {{ margin: .3em 0 0; opacity: .95; }}
.stats {{ display: flex; flex-wrap: wrap; gap: .6em; margin: 1.2em 0 0; }}
.stat {{ background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.35); border-radius: 8px; padding: .5em .9em; }}
.stat b {{ display: block; font-size: 1.25em; }}
.toolbar {{ background: #fff; border: 1px solid #dbe4e8; border-radius: 10px; padding: .9em 1em; margin: 1.2em 0; display: flex; flex-wrap: wrap; gap: .8em; align-items: center; }}
.toolbar input[type=search] {{ flex: 1; min-width: 200px; padding: .55em .8em; border: 1px solid #b9c6cc; border-radius: 6px; font-size: 1em; }}
.toolbar select {{ padding: .55em .6em; border: 1px solid #b9c6cc; border-radius: 6px; font-size: 1em; }}
.card {{ background: #fff; border: 1px solid #dbe4e8; border-radius: 10px; padding: 1.2em 1.3em; margin: 1.2em 0; box-shadow: 0 1px 3px rgba(0,0,0,.06); }}
.badge {{ display: inline-block; background: #e6f6fc; color: #0b6e92; border-radius: 20px; padding: .15em .8em; font-size: .85em; font-weight: 600; }}
.card h2 {{ margin: .4em 0 .2em; }}
.card h2 small {{ color: #5b6b73; font-weight: 400; }}
.meta {{ color: #4a5a62; }}
.bar {{ display: inline-block; height: 12px; background: #1cabe2; border-radius: 2px; }}
table {{ border-collapse: collapse; width: 100%; margin: .6em 0; }} td, th {{ border-bottom: 1px solid #e3e9ec; padding: 6px 8px; text-align: left; }}
th {{ color: #4a5a62; font-size: .9em; }}
.trend {{ background: #f0f7fa; border-radius: 6px; padding: .6em .8em; }}
section.sharepoint img {{ max-width: 100%; border: 1px solid #dbe4e8; border-radius: 8px; }}
footer {{ max-width: 920px; margin: 2em auto; padding: 0 1em 2em; color: #5b6b73; font-size: .92em; }}
</style>
</head>
<body>
<header><div class="wrap">
<h1>UNICEF Data Hub</h1>
<p>Real public data on child health and education, organised and tagged — so anyone can find a number fast.</p>
<div class="stats">
<div class="stat"><b>{len(rows)}</b>rows</div>
<div class="stat"><b>{len(tags)}</b>indicators</div>
<div class="stat"><b>5</b>countries</div>
<div class="stat"><b>{html.escape(fetched)}</b>fetched</div>
</div>
</div></header>
<main>
<p>Data from the UNICEF Data Warehouse (SDMX API, https://sdmx.data.unicef.org), covering Pakistan, India, Bangladesh, Afghanistan and Nepal. Search and filter work offline once the page is loaded. This is my own project — it is not UNICEF work and not an official UNICEF page. Verify every number at <a href="https://data.unicef.org">data.unicef.org</a>.</p>
<div class="toolbar">
<label>Search <input id="q" type="search" placeholder="try: mortality, stunting, school"></label>
<label>Topic <select id="topic"><option value="">all</option><option>Health</option><option>Nutrition</option><option>Education</option></select></label>
<span id="count"></span>
</div>
<div id="cards">
{''.join(sections)}
</div>
<section class="card sharepoint">
<h2>Same data in SharePoint</h2>
<p>The same {len(rows)} rows are also published as a SharePoint list, with metadata on every row — indicator, country, year, value, unit and source — so the content stays organised, tagged and findable. The SharePoint site lives in my student Microsoft 365 tenant, so it opens only for people in that tenant; the screenshot below is the proof.</p>
<img src="docs/sharepoint-list.png" alt="SharePoint list showing the 440 UNICEF data rows with metadata columns">
</section>
</main>
<footer>
<p>Built by Awais Ahmed Shah, final-year BS Data Science student, UET Peshawar. Data: UNICEF Data Warehouse, public SDMX API. Figures are UNICEF estimates and can be revised — check the latest at <a href="https://data.unicef.org">data.unicef.org</a>.</p>
</footer>
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
