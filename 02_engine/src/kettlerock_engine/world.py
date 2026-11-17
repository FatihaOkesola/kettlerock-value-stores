"""Milestone 2: draw the sealed world from a private seed.

Every value drawn here is hidden from the analyst until the season ends. The draw
reads its ranges, distributions and rules from calibrated_parameters.csv and writes
one canonical file, so the same seed always produces the same bytes.

Random streams are named: each group of draws (remodel lifts, price response, events
and so on) has its own stream derived from the seed and the group's name. Adding a
new group later never changes the values already drawn for the others.
"""
from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .params import Params

DECIMALS = 10                      # fixed decimal places for every sealed number
SEALED_COLUMNS = ["record_type", "sealed_parameter_id", "scope", "field", "value"]

# Event type names as used in the sealed log
COMPETITOR = "competitor_opening"
SUPPLIER = "supplier_cost_increase"
FREIGHT = "freight_cost_spike"
SEASONAL = "seasonal_sell_through_miss"
LOCAL = "local_demand_shock"
DISRUPTION = "store_disruption"
OTHER_TYPES = [LOCAL, SEASONAL, FREIGHT, DISRUPTION]       # EV-12: drawn without replacement
SEVERE = {COMPETITOR, SUPPLIER, FREIGHT, SEASONAL}         # EV-09
COMPANY_WIDE = {SUPPLIER, FREIGHT, SEASONAL}               # no market (EV-09)

# Timing window (EV-11) and limits (EV-09, EV-10, EV-16). The values are stated in
# those parameter rows; they are repeated here as named constants and checked
# against the parameter text by the tests, so the code and the file cannot drift.
WINDOW_START = date(2024, 2, 4)
WINDOW_END = date(2026, 9, 5)
SUPPLIER_OCCUPANCY_WEEKS = 13
SAME_MARKET_GAP_DAYS = 365
MAX_STARTS_PER_QUARTER = 2
MAX_ATTEMPTS = 10_000
COVERAGE_YEARS = (2025, 2026, 2027)


def seed_from_hex(seed_hex: str) -> int:
    s = seed_hex.strip().lower()
    if len(s) != 64 or any(c not in "0123456789abcdef" for c in s):
        raise ValueError("The seed must be 64 hexadecimal characters (256 bits).")
    return int(s, 16)


def stream(seed: int, name: str) -> np.random.Generator:
    """A random stream for one named group of draws."""
    key = int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:16], 16)
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(entropy=seed, spawn_key=(key,))))


def fmt(x: float) -> str:
    v = f"{x:.{DECIMALS}f}"
    return "0." + "0" * DECIMALS if v.startswith("-0.") and float(v) == 0 else v


def _uniform(rng, lo, hi):
    return float(rng.uniform(lo, hi))


def _truncated_normal(rng, mean, sd, lo, hi):
    while True:                                  # deterministic: advances the stream
        x = float(rng.normal(mean, sd))
        if lo <= x <= hi:
            return x


# ---------------------------------------------------------------- parameter draws

def draw_parameters(seed: int, params: Params, tables: dict) -> list[tuple]:
    rows: list[tuple] = []
    add = lambda sid, scope, fld, val: rows.append(("parameter", sid, scope, fld, val))
    stores = tables["dim_store"]
    products = tables["dim_product"]

    # SE-19: remodel lift per remodel, applied to transactions
    rng = stream(seed, "remodel_lift")
    lo, hi = params.bounds("SE-19")
    for _, s in stores[stores.remodel_reopen_date.astype(str) != ""].sort_values("store_id").iterrows():
        if pd.isna(s.remodel_reopen_date) or str(s.remodel_reopen_date) in ("", "nan"):
            continue
        add("SWP-REMODEL-LIFT", f"{s.store_id}|{s.remodel_reopen_date}", "lift_pct", fmt(_uniform(rng, lo, hi)))

    # PR-01 to PR-03: item price response, uniform within the category range
    rng = stream(seed, "price_response")
    by_cat = {"Consumables": ("PR-01", "SWP-PRICE-CONSUMABLES"),
              "General merchandise": ("PR-02", "SWP-PRICE-GENERAL"),
              "Seasonal": ("PR-03", "SWP-PRICE-SEASONAL")}
    for _, p in products.sort_values("product_id").iterrows():
        pid, sid = by_cat[p.category]
        lo, hi = params.bounds(pid)
        add(sid, p.product_id, "price_response", fmt(_uniform(rng, lo, hi)))

    # PR-04: store multiplier by location type (fixed values, sealed with the world)
    for part in params.row("PR-04")["central_value"].split(";"):
        loc, val = part.strip().rsplit(" ", 1)
        add("SWP-PRICE-STORE", loc.replace(" ", "_"), "multiplier", fmt(float(val)))

    # PR-06, CAL-05, MAC-10: one value per seed
    for pid, sid, name, fld in [("PR-06", "SWP-PRICE-TRAFFIC", "price_traffic", "share"),
                                ("CAL-05", "SWP-RECAPTURE", "recapture", "share"),
                                ("MAC-10", "SWP-TRADE-DOWN", "trade_down", "response")]:
        lo, hi = params.bounds(pid)
        add(sid, "company", fld, fmt(_uniform(stream(seed, name), lo, hi)))

    # VAR-01: store level factor, lognormal with mean 1
    rng = stream(seed, "store_level")
    sigma = params.value("VAR-01")
    for sid in sorted(stores.store_id):
        add("SWP-STORE-LEVEL", sid, "level_factor", fmt(float(np.exp(rng.normal(-sigma ** 2 / 2, sigma)))))

    # GR-01, GR-02: underlying comparable growth by fiscal year, truncated normal
    for pid, sid, name in [("GR-01", "SWP-COMP-TRX", "comp_transactions"),
                           ("GR-02", "SWP-COMP-TKT", "comp_ticket")]:
        rng = stream(seed, name)
        lo, hi = params.bounds(pid)
        sd = (hi - lo) / 4
        for fy in COVERAGE_YEARS:
            add(sid, f"FY{fy}", "growth_pct", fmt(_truncated_normal(rng, params.value(pid), sd, lo, hi)))
    return rows


# ---------------------------------------------------------------- hidden events

@dataclass
class Event:
    type: str
    start: date
    occupancy_end: date | None          # end of the severe-event occupancy, if severe
    active_end: date                    # end of the store- or market-level effect window
    market: str | None = None
    stores: tuple = ()
    details: dict = field(default_factory=dict)


def _sundays(lo: date, hi: date) -> list[date]:
    d = lo + timedelta(days=(6 - lo.weekday()) % 7)
    out = []
    while d <= hi:
        out.append(d)
        d += timedelta(days=7)
    return out


def _easter(y: int) -> date:
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    return date(y, (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1)


def seasonal_windows() -> list[tuple[str, date, date]]:
    """Seasonal selling windows (DS-07 to DS-11) whose start falls inside the event window."""
    out = []
    for y in range(2024, 2027):
        e = _easter(y)
        out += [("Halloween", date(y, 8, 15), date(y, 10, 31)),
                ("Christmas", date(y, 11, 1), date(y, 12, 24)),
                ("Easter", e - timedelta(weeks=6), e + timedelta(days=1)),
                ("Summer", date(y, 5, 15), date(y, 8, 15)),
                ("Back-to-school", date(y, 7, 15), date(y, 9, 15))]
    return sorted(w for w in out if WINDOW_START <= w[1] <= WINDOW_END)


def _candidate(rng, types, params, stores, markets, departments, sundays, windows) -> list[Event]:
    events = []
    for t in types:
        if t == SEASONAL:
            name, ws, we = windows[rng.integers(len(windows))]
            lo, hi = params.bounds("EV-05")
            events.append(Event(t, ws, we, we, details={"window": name, "window_start": ws, "window_end": we,
                                                         "unit_shortfall_pct": _uniform(rng, lo, hi)}))
            continue
        start = sundays[rng.integers(len(sundays))]
        open_stores = stores[pd.to_datetime(stores.open_date).dt.date <= start]
        if t == COMPETITOR:
            open_markets = sorted(set(open_stores.market_id) & set(markets))
            m = open_markets[rng.integers(len(open_markets))]
            months = _uniform(rng, *params.bounds("EV-03"))
            end = start + timedelta(days=round(months * 365.25 / 12))
            loss = _uniform(rng, *params.bounds("EV-02"))
            st = tuple(sorted(open_stores[open_stores.market_id == m].store_id))
            events.append(Event(t, start, end, end, m, st, {"initial_loss_pct": loss, "recovery_months": months,
                                                           "permanent_loss_pct": loss * params.value("EV-13")}))
        elif t == SUPPLIER:
            dept = departments[rng.integers(len(departments))]
            occ = start + timedelta(weeks=SUPPLIER_OCCUPANCY_WEEKS) - timedelta(days=1)
            events.append(Event(t, start, occ, occ, details={"department_id": dept,
                                                             "cost_increase_pct": _uniform(rng, *params.bounds("EV-06"))}))
        elif t == FREIGHT:
            weeks = int(rng.integers(int(params.bounds("EV-15")[0]), int(params.bounds("EV-15")[1]) + 1))
            end = start + timedelta(weeks=weeks) - timedelta(days=1)
            events.append(Event(t, start, end, end, details={"freight_increase_pct": _uniform(rng, *params.bounds("EV-07")),
                                                             "duration_weeks": weeks}))
        elif t == LOCAL:
            weeks = int(rng.integers(int(params.bounds("EV-14")[0]), int(params.bounds("EV-14")[1]) + 1))
            end = start + timedelta(weeks=weeks) - timedelta(days=1)
            size = _uniform(rng, *params.bounds("EV-04"))
            direction = "up" if rng.integers(2) == 1 else "down"
            if rng.integers(2) == 1:                        # one market
                open_markets = sorted(set(open_stores.market_id) & set(markets))
                m = open_markets[rng.integers(len(open_markets))]
                st = tuple(sorted(open_stores[open_stores.market_id == m].store_id))
                scope = "market"
            else:                                           # one store
                s = open_stores.sort_values("store_id").iloc[rng.integers(len(open_stores))]
                m, st, scope = s.market_id, (s.store_id,), "store"
            events.append(Event(t, start, None, end, m, st, {"scope": scope, "direction": direction,
                                                             "size_pct": size, "duration_weeks": weeks}))
        elif t == DISRUPTION:
            lo, hi = params.bounds("EV-08")
            days = int(rng.integers(int(lo), int(hi) + 1))
            s = open_stores.sort_values("store_id").iloc[rng.integers(len(open_stores))]
            end = start + timedelta(days=days - 1)
            events.append(Event(t, start, None, end, s.market_id, (s.store_id,), {"closed_days": days}))
    return events


def check_rules(events: list[Event], quarter_of) -> list[str]:
    """Return the rules a candidate schedule breaks (empty list = valid)."""
    broken = []
    if any(not (WINDOW_START <= e.start <= WINDOW_END) for e in events):
        broken.append("timing window")
    years = {quarter_of(e.start)[0] for e in events}
    if not set(COVERAGE_YEARS) <= years:
        broken.append("coverage by fiscal year")
    starts = pd.Series([quarter_of(e.start) for e in events]).value_counts()
    if (starts > MAX_STARTS_PER_QUARTER).any():
        broken.append("starts per quarter")
    severe = sorted((e.start, e.occupancy_end) for e in events if e.type in SEVERE)
    if any(b[0] <= a[1] for a, b in zip(severe, severe[1:])):
        broken.append("severe overlap")
    local = [e for e in events if e.type not in COMPANY_WIDE]
    for i, a in enumerate(local):
        for b in local[i + 1:]:
            if set(a.stores) & set(b.stores) and a.start <= b.active_end and b.start <= a.active_end:
                broken.append("store carries two events")
            if a.market == b.market and abs((a.start - b.start).days) < SAME_MARKET_GAP_DAYS:
                broken.append("same market within 12 months")
    return broken


def draw_events(seed: int, params: Params, tables: dict) -> list[Event]:
    rng = stream(seed, "events")
    lo, hi = params.bounds("EV-01")
    n = int(rng.integers(int(lo), int(hi) + 1))
    types = [COMPETITOR, SUPPLIER] + list(rng.choice(OTHER_TYPES, size=n - 2, replace=False))
    stores = tables["dim_store"]
    markets = sorted(tables["dim_market"].market_id)
    departments = sorted(tables["dim_product"].department_id.unique())
    sundays = _sundays(WINDOW_START, WINDOW_END)
    windows = seasonal_windows()
    dd = tables["dim_date"].assign(d=lambda x: pd.to_datetime(x.date).dt.date).set_index("d")
    quarter_of = lambda d: (int(dd.at[d, "fiscal_year"]), int(dd.at[d, "fiscal_quarter"]))
    for _ in range(MAX_ATTEMPTS):
        cand = _candidate(rng, types, params, stores, markets, departments, sundays, windows)
        if not check_rules(cand, quarter_of):
            return sorted(cand, key=lambda e: (e.start, e.type))
    raise RuntimeError(f"No valid event schedule after {MAX_ATTEMPTS} candidates; the rules cannot be met.")


def event_rows(events: list[Event]) -> list[tuple]:
    rows = []
    for i, e in enumerate(events, 1):
        eid = f"EVT-{i:02d}"
        rec = {"type": e.type, "start_date": e.start.isoformat(),
               "end_date": "" if e.type == SUPPLIER else e.active_end.isoformat(),
               "market_id": e.market or "", "stores": ";".join(e.stores)}
        for k, v in e.details.items():
            rec[k] = v.isoformat() if isinstance(v, date) else (fmt(v) if isinstance(v, float) else str(v))
        rows += [("event", "SWP-EVENTS", eid, k, str(v)) for k, v in rec.items()]
    return rows


# ---------------------------------------------------------------- the sealed file

def draw_world(seed_hex: str, params: Params, tables: dict) -> bytes:
    """All sealed values as canonical bytes: UTF-8, sorted rows, fixed decimals, \\n, no timestamps."""
    seed = seed_from_hex(seed_hex)
    rows = draw_parameters(seed, params, tables) + event_rows(draw_events(seed, params, tables))
    rows.sort(key=lambda r: (r[0], r[1], r[2], r[3]))
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(SEALED_COLUMNS)
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")
