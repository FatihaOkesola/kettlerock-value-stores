"""One-off authoring script for the store master (config/structure/stores_master.csv).

The store master is authored structure: it follows the store timeline and market
layout in sections 3 and 5 of the specification. The script is kept so the file can
be traced, but the frozen CSV is the source the engine reads; re-running the script
must reproduce it byte for byte.
"""
from pathlib import Path
import csv

OUT = Path(__file__).resolve().parents[1] / "config" / "structure" / "stores_master.csv"

# (market_id, region, province, city, location_type, open_date, status)
# Region totals at the end of Q3 FY2027: GTA 14, Southwestern Ontario 12, Montreal 9, Atlantic 5.
STORES = [
    # Greater Toronto Area: 5 markets (3, 3, 3, 3, 2)
    ("GTA-1", "Greater Toronto Area", "ON", "Brampton", "suburban", "2009-04-18", "open"),
    ("GTA-1", "Greater Toronto Area", "ON", "Brampton", "suburban", "2013-06-08", "open"),
    ("GTA-1", "Greater Toronto Area", "ON", "Brampton", "urban", "2018-05-12", "open"),
    ("GTA-2", "Greater Toronto Area", "ON", "Scarborough", "urban", "2009-09-12", "open"),
    ("GTA-2", "Greater Toronto Area", "ON", "Scarborough", "urban", "2012-10-13", "open"),
    ("GTA-2", "Greater Toronto Area", "ON", "Scarborough", "suburban", "2022-03-19", "open"),
    ("GTA-3", "Greater Toronto Area", "ON", "Mississauga", "suburban", "2010-08-21", "open"),
    ("GTA-3", "Greater Toronto Area", "ON", "Mississauga", "suburban", "2017-04-08", "open"),
    ("GTA-3", "Greater Toronto Area", "ON", "Mississauga", "urban", "2022-09-17", "open"),
    ("GTA-4", "Greater Toronto Area", "ON", "Oshawa", "suburban", "2014-05-10", "open"),
    ("GTA-4", "Greater Toronto Area", "ON", "Oshawa", "suburban", "2019-08-24", "open"),
    ("GTA-4", "Greater Toronto Area", "ON", "Oshawa", "urban", "2024-04-13", "open"),
    ("GTA-5", "Greater Toronto Area", "ON", "Vaughan", "suburban", "2023-05-13", "open"),
    ("GTA-5", "Greater Toronto Area", "ON", "Vaughan", "suburban", "2025-09-13", "open"),
    # Southwestern Ontario: 8 markets (2, 2, 2, 2, 1, 1, 1, 1)
    ("SWO-1", "Southwestern Ontario", "ON", "London", "suburban", "2009-11-07", "open"),
    ("SWO-1", "Southwestern Ontario", "ON", "London", "urban", "2016-09-17", "open"),
    ("SWO-2", "Southwestern Ontario", "ON", "Kitchener", "suburban", "2011-05-14", "open"),
    ("SWO-2", "Southwestern Ontario", "ON", "Kitchener", "urban", "2018-09-08", "open"),
    ("SWO-3", "Southwestern Ontario", "ON", "Hamilton", "urban", "2012-04-21", "open"),
    ("SWO-3", "Southwestern Ontario", "ON", "Hamilton", "suburban", "2020-10-17", "open"),
    ("SWO-4", "Southwestern Ontario", "ON", "Windsor", "suburban", "2017-10-14", "open"),
    ("SWO-4", "Southwestern Ontario", "ON", "Windsor", "suburban", "2023-03-18", "open"),
    ("SWO-5", "Southwestern Ontario", "ON", "Woodstock", "small town", "2018-11-10", "open"),
    ("SWO-6", "Southwestern Ontario", "ON", "Stratford", "small town", "2022-04-23", "open"),
    ("SWO-7", "Southwestern Ontario", "ON", "Sarnia", "small town", "2023-09-16", "open"),
    ("SWO-8", "Southwestern Ontario", "ON", "Chatham", "small town", "2024-08-17", "open"),
    # Montreal area: 4 markets (3, 2, 2, 2)
    ("MTL-1", "Montreal area", "QC", "Laval", "suburban", "2015-05-09", "open"),
    ("MTL-1", "Montreal area", "QC", "Laval", "suburban", "2019-04-13", "open"),
    ("MTL-1", "Montreal area", "QC", "Laval", "urban", "2024-05-11", "open"),
    ("MTL-2", "Montreal area", "QC", "Montreal", "urban", "2013-09-14", "open"),
    ("MTL-2", "Montreal area", "QC", "Montreal", "urban", "2021-08-21", "open"),
    ("MTL-3", "Montreal area", "QC", "Longueuil", "suburban", "2016-04-16", "open"),
    ("MTL-3", "Montreal area", "QC", "Longueuil", "suburban", "2023-10-21", "open"),
    ("MTL-4", "Montreal area", "QC", "Terrebonne", "suburban", "2022-11-12", "open"),
    ("MTL-4", "Montreal area", "QC", "Terrebonne", "suburban", "2025-10-18", "open"),
    # Atlantic Canada: 4 markets (Halifax 2; three single-store towns)
    ("ATL-1", "Atlantic Canada", "NS", "Halifax", "urban", "2024-10-19", "open"),
    ("ATL-1", "Atlantic Canada", "NS", "Halifax", "suburban", "2026-05-09", "open"),
    ("ATL-2", "Atlantic Canada", "NB", "Moncton", "small town", "2025-06-14", "open"),
    ("ATL-3", "Atlantic Canada", "NB", "Fredericton", "small town", "2026-07-11", "open"),
    ("ATL-4", "Atlantic Canada", "NS", "Truro", "small town", "2026-09-19", "open"),
    # Planned Q4 FY2027 openings (Ontario, GTA)
    ("GTA-5", "Greater Toronto Area", "ON", "Vaughan", "urban", "2026-11-21", "planned"),
    ("GTA-6", "Greater Toronto Area", "ON", "Markham", "suburban", "2027-01-16", "planned"),
]

# Historical remodels (about three a year): each store is remodelled when its lease is renewed,
# reopening on the first Saturday at least four weeks after the renewal date. One remodel per store.
REMODELS = {"KVS001": "2024-05-18", "KVS010": "2024-06-08", "KVS004": "2024-10-12", "KVS015": "2024-12-07", "KVS027": "2025-06-07", "KVS007": "2025-09-20", "KVS032": "2026-05-16", "KVS017": "2026-06-13", "KVS016": "2026-10-17"}


def lease_terms(open_date: str):
    """Ten-year base term from opening, then five-year renewals; current term as at the Q3 FY2027 close (2026-10-31)."""
    y, m, d = (int(x) for x in open_date.split("-"))
    start_year, end_year = y, y + 10
    renewals = 0
    while f"{end_year:04d}-{m:02d}-{d:02d}" <= "2026-10-31":
        start_year, end_year = end_year, end_year + 5
        renewals += 1
    return f"{start_year:04d}-{m:02d}-{d:02d}", f"{end_year:04d}-{m:02d}-{d:02d}", renewals


def main():
    rows = []
    for i, (market, region, prov, city, loc, opened, status) in enumerate(STORES, start=1):
        sid = f"KVS{i:03d}"
        fmt = "compact" if region == "Atlantic Canada" else "standard"
        sqft = 6000 if fmt == "compact" else 9000
        start, end, renewals = lease_terms(opened)
        rows.append({
            "store_id": sid, "store_name": f"Kettlerock {city} {i:03d}", "market_id": market,
            "region": region, "province": prov, "city": city, "location_type": loc,
            "format": fmt, "selling_sq_ft": sqft, "open_date": opened, "status": status,
            "cohort_year": int(opened[:4]), "lease_term_start": start, "lease_term_end": end,
            "lease_renewals_taken": renewals, "remodel_reopen_date": REMODELS.get(sid, ""),
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} stores written to {OUT}")


if __name__ == "__main__":
    main()
