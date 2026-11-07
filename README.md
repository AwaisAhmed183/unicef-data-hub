# UNICEF Data Hub

**Live demo — open it and try the search: https://awaisahmed183.github.io/unicef-data-hub/**

A small, real, live hub of UNICEF public data. It fetches real numbers
from the UNICEF Data Warehouse (SDMX API, https://sdmx.data.unicef.org),
tags them, and builds a searchable hub page with latest values and a
Pakistan trend for each indicator.

## Indicators (3, all public)

- `CME_MRY0T4` — Under-five mortality rate (deaths per 1,000 live births)
- `NT_ANT_HAZ_NE2` — Height-for-age <-2 SD (stunting), % of children under 5
- `ED_ROFST_L1` — Out-of-school rate for children of primary school age, %

Countries: Pakistan, India, Bangladesh, Afghanistan, Nepal.
Total only (both sexes, all wealth groups). Fetched 7 Nov 2026 — 440 rows.

Pakistan, latest: under-5 mortality 56.0 per 1,000 (2024); stunting
37.6% (2018); out-of-school, primary 23.0% (2018). Check every number
at https://data.unicef.org — UNICEF's figures are estimates and can
be revised.

## Run it

```bash
pip install unicefdata pandas
python3 fetch_data.py   # live fetch from UNICEF, writes data.csv
python3 build_hub.py    # checks the data, writes index.html
# then open index.html in any browser — search and filter work offline
```

## What this is, honestly

Practice built to practise the tagging and hub tasks in UNICEF Job
596601 (Supporter Content – Knowledge Management Intern, Division of
Private Fundraising and Partnerships): organising content so people in
any time zone can find it, tagging it with metadata, and keeping it
up to date.

It is **not** UNICEF work, **not** SharePoint, and **not** WeShare.
No UNICEF content or branding is used beyond the public data itself,
credited to its source. Author: Awais Ahmed Shah, final-year BS Data
Science student, UET Peshawar.
