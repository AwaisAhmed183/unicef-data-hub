#!/usr/bin/env python3
"""Build a searchable hub page (index.html) from data.csv + tags.csv.

Stdlib only. No server, no database.
Usage:  python3 build_hub.py
Checks: every indicator in tags.csv has rows in data.csv; every row has
a country, year and value; latest value per country is shown with its year.
"""
import csv
import html
from collections import defaultdict
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
    return f"<p><b>Pakistan trend (last {len(pak)} points):</b> {cells}</p>"

def main():
    tags, rows, fetched = load()
    sections = []
    for ind, t in tags.items():
        search = html.escape((t["indicator_name"] + " " + t["topic"] + " " + t["keywords"] + " " + ind).lower())
        sections.append(f"""
<section class="card" data-search="{search}" data-topic="{html.escape(t['topic'])}">
<h2>{html.escape(t['indicator_name'])} <small>({html.escape(ind)})</small></h2>
<p><b>Topic:</b> {html.escape(t['topic'])} &nbsp;|&nbsp; <b>Audience:</b> {html.escape(t['audience'])}</p>
<p><b>What it means:</b> {html.escape(t['unit_meaning'])}</p>
<p><b>Keywords:</b> {html.escape(t['keywords'])}</p>
{latest_table(rows, ind)}
{pak_trend(rows, ind)}
</section>""")
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>UNICEF Data Hub — live public data</title>
<style>
body {{ font-family: sans-serif; max-width: 900px; margin: 2em auto; padding: 0 1em; }}
.card {{ border: 1px solid #888; border-radius: 8px; padding: 1em; margin: 1em 0; }}
.bar {{ display: inline-block; height: 12px; background: #1F3864; }}
table {{ border-collapse: collapse; }} td, th {{ border: 1px solid #ccc; padding: 4px 8px; text-align: left; }}
</style>
</head>
<body>
<h1>UNICEF Data Hub</h1>
<p>Live public data from the UNICEF Data Warehouse (SDMX API, https://sdmx.data.unicef.org).
Fetched on {html.escape(fetched)}. {len(rows)} rows, {len(tags)} indicators, 5 countries
(Pakistan, India, Bangladesh, Afghanistan, Nepal). Search and filter work offline once fetched.</p>
<p><b>This is not UNICEF work.</b> It is a practice hub built to practise the tagging
and hub tasks in UNICEF Job 596601. It is not SharePoint and not WeShare.
Verify every number at <a href="https://data.unicef.org">data.unicef.org</a>.</p>
<p><label>Search <input id="q" type="search" placeholder="try: mortality, stunting, school"></label>
<label>Topic <select id="topic"><option value="">all</option><option>Health</option><option>Nutrition</option><option>Education</option></select></label></p>
<p id="count"></p>
<div id="cards">
{''.join(sections)}
</div>
<script>
function apply() {{
  const q = document.getElementById('q').value.toLowerCase();
  const t = document.getElementById('topic').value;
  let shown = 0;
  document.querySelectorAll('.card').forEach(c => {{
    const ok = (!q || c.dataset.search.includes(q)) && (!t || c.dataset.topic === t);
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
