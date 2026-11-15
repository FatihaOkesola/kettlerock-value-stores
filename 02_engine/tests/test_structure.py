"""Structure tables match specification sections 3 to 6 and the calibrated parameters."""
import pandas as pd


def open_at(stores, day):
    return stores[(stores.status == "open") & (stores.open_date <= day)]


def test_store_timeline(tables):
    s = tables["dim_store"]
    assert len(open_at(s, "2024-02-03")) == 30
    assert open_at(s, "2024-02-03").province.value_counts().to_dict() == {"ON": 23, "QC": 7}
    for (a, b), n in {("2024-02-04", "2025-02-01"): 4, ("2025-02-02", "2026-01-31"): 3,
                      ("2026-02-01", "2026-10-31"): 3}.items():
        assert ((s.status == "open") & (s.open_date >= a) & (s.open_date <= b)).sum() == n


def test_footprint_end_q3_fy2027(tables):
    s = open_at(tables["dim_store"], "2026-10-31")
    assert len(s) == 40
    assert s.region.value_counts().to_dict() == {
        "Greater Toronto Area": 14, "Southwestern Ontario": 12, "Montreal area": 9, "Atlantic Canada": 5}
    assert (s[s.region == "Atlantic Canada"].format == "compact").all()


def test_markets(tables):
    s = open_at(tables["dim_store"], "2026-10-31")
    sizes = s.groupby("market_id").size()
    assert len(sizes) == 21 and sizes.max() <= 3
    assert sorted(sizes[sizes.index.str.startswith("GTA")].tolist()) == [2, 3, 3, 3, 3]


def test_two_planned_ontario_openings(tables):
    p = tables["dim_store"][tables["dim_store"].status == "planned"]
    assert len(p) == 2 and (p.province == "ON").all()
    assert p.open_date.between("2026-11-01", "2027-01-30").all()


def test_occupancy_near_target(tables, params):
    s = open_at(tables["dim_store"], "2026-10-31")
    mature = params.value("SE-03")
    sales = s.format.map({"standard": mature, "compact": mature * params.value("SE-04")})
    occ = s.annual_occupancy_cost.astype(float).sum() / sales.sum() * 100
    assert abs(occ - params.value("SE-11")) <= 0.5


def test_products(tables, params):
    p = tables["dim_product"]
    assert len(p) == 180 and p.product_id.is_unique
    m = p.groupby("category").product_margin_at_ticket.apply(lambda x: x.astype(float).mean())
    for cat, pid in {"Consumables": "MP-05", "General merchandise": "MP-06", "Seasonal": "MP-07"}.items():
        assert abs(m[cat] * 100 - params.value(pid)) < 0.05
    assert set(p.price_point.astype(float)) <= {1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0}


def test_import_share_of_cogs(tables, params):
    p = tables["dim_product"].copy()
    p["m"] = p.product_margin_at_ticket.astype(float)
    shares = {"Consumables": params.value("MP-02"), "General merchandise": params.value("MP-03"),
              "Seasonal": params.value("MP-04")}
    cogs = {c: shares[c] * (1 - p[p.category == c].m.mean()) for c in shares}
    imp = {c: p[p.category == c].import_flag.astype(int).mean() for c in shares}
    share = sum(cogs[c] * imp[c] for c in shares) / sum(cogs.values()) * 100
    lo, hi = params.bounds("MP-13")
    assert lo <= share <= hi


def test_average_unit_price_matches_basket(tables, params):
    p = tables["dim_product"]
    price = p.groupby("category").price_point.apply(lambda x: x.astype(float).mean())
    shares = {"Consumables": params.value("MP-02"), "General merchandise": params.value("MP-03"),
              "Seasonal": params.value("MP-04")}
    avg = sum(shares.values()) / sum(shares[c] / price[c] for c in shares)
    assert abs(avg - params.value("SE-06") / 4.3) < 0.10
