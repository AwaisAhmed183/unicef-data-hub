#!/usr/bin/env python3
"""Fetch real UNICEF data, live, from the UNICEF Data Warehouse (SDMX API).

Uses the `unicefdata` package (UNICEF Data and Analytics Section).
No key, no login. Source: https://sdmx.data.unicef.org

Indicators (all public, verified 7 Nov 2026 via search_indicators):
  CME_MRY0T4   Under-five mortality rate (deaths per 1,000 live births)
  NT_ANT_HAZ_NE2  Height-for-age <-2 SD (stunting), % of children under 5
  ED_ROFST_L1  Out-of-school rate for children of primary school age, %

Countries: Pakistan, India, Bangladesh, Afghanistan, Nepal.
Filter: total only (sex _T, wealth _T). No modelled / split rows.
Output: data.csv with one row per country + indicator + year, plus
fetched_on (today, Asia/Karachi) and the source for every row.
Run:  python3 fetch_data.py   (needs: pip install unicefdata pandas)
"""
import datetime
import pandas as pd
from unicefdata import unicefData

INDICATORS = ["CME_MRY0T4", "NT_ANT_HAZ_NE2", "ED_ROFST_L1"]
COUNTRIES = ["PAK", "IND", "BGD", "AFG", "NPL"]
FETCHED_ON = datetime.date.today().isoformat()

frames = []
for code in INDICATORS:
    df = unicefData(indicator=code, countries=COUNTRIES)
    df = df[(df["sex"] == "_T") & (df["wealth_quintile"] == "_T")]
    keep = df[["indicator", "indicator_name", "iso3", "country", "period", "value", "unit", "data_source"]].copy()
    keep = keep.rename(columns={"period": "year", "iso3": "country_code"})
    keep["year"] = keep["year"].astype(int)
    keep["fetched_on"] = FETCHED_ON
    keep["source_url"] = "https://sdmx.data.unicef.org"
    frames.append(keep)
    print(code, "rows kept:", len(keep), "| years:", int(keep["year"].min()), "-", int(keep["year"].max()))

out = pd.concat(frames, ignore_index=True).sort_values(["indicator", "country", "year"])
out.to_csv("data.csv", index=False)
print("WROTE data.csv rows:", len(out))
print(out.groupby(["indicator", "country"])["year"].max())
