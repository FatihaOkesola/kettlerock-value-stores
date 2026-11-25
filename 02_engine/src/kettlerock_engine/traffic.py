"""Milestone 3: daily transactions for every store, from the start of FY2025 to the Q3 FY2027 close.

The day's expected transactions are built in four stages, each testable on its own:

1. Underlying demand: base level x store strength x ramp-up x growth x day of week x month
   x trade-down x events and remodels. Remodel and unplanned closures set the day to zero.
2. Holiday mechanics: holiday closures, reduced hours, the pre-holiday lift and recapture,
   with only the larger of the lift and the recapture on any one day (CAL-07).
3. Month neutrality (TR-02): each store-month is rescaled so holiday mechanics move demand
   between days but never change the month's expected total.
4. Noise: weekly store drift (TR-06), then an integer Poisson count for the day (TR-07).

Only the date, store, trading status and transaction count are published. The components
behind each number stay inside the engine.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .params import Params
from .world import stream, seed_from_hex, COMPETITOR, LOCAL, DISRUPTION

# Rules stated in the parameter file (TR-03, TR-04); the tests check this text matches
RAMP_YEARS = [0.0, 1.0, 2.0, 3.0]
RAMP_LEVELS = [0.60, 0.80, 0.90, 1.00]
REMODEL_CLOSED_DAYS = 7
EXTENDED_CLOSURE_DAYS = 14          # CMP-01

STATUS_OPEN, STATUS_REDUCED = "open", "reduced_hours"
STATUS_HOLIDAY, STATUS_REMODEL, STATUS_UNPLANNED = "closed_holiday", "closed_remodel", "closed_unplanned"
PROVINCE_NAME = {"ON": "Ontario", "QC": "Quebec", "NS": "Nova Scotia", "NB": "New Brunswick"}


# ---------------------------------------------------------------- inputs

@dataclass
class Sealed:
    """The sealed values this step reads, parsed from the canonical sealed file."""
    level: dict
    remodel_lift: dict
    comp_trx: dict
    trade_down: float
    recapture: float
    events: pd.DataFrame


def read_sealed(sealed_bytes: bytes) -> Sealed:
    s = pd.read_csv(io.BytesIO(sealed_bytes), dtype=str, keep_default_na=False)
    p = s[s.record_type == "parameter"]
    get = lambda sid: p[p.sealed_parameter_id == sid]
    ev = s[s.record_type == "event"].pivot(index="scope", columns="field", values="value")
    return Sealed(
        level=dict(zip(get("SWP-STORE-LEVEL").scope, get("SWP-STORE-LEVEL").value.astype(float))),
        remodel_lift={k.split("|")[0]: (date.fromisoformat(k.split("|")[1]), v / 100)
                      for k, v in zip(get("SWP-REMODEL-LIFT").scope, get("SWP-REMODEL-LIFT").value.astype(float))},
        comp_trx={int(k[2:]): v / 100 for k, v in zip(get("SWP-COMP-TRX").scope, get("SWP-COMP-TRX").value.astype(float))},
        trade_down=float(get("SWP-TRADE-DOWN").value.iloc[0]),
        recapture=float(get("SWP-RECAPTURE").value.iloc[0]),
        events=ev,
    )


def history_window(dim_date: pd.DataFrame, last_fy: int, last_q: int) -> tuple[date, date]:
    d = dim_date.assign(d=pd.to_datetime(dim_date.date).dt.date)
    start = d.d.min()
    end = d[(d.fiscal_year == last_fy) & (d.fiscal_quarter == last_q)].d.max()
    return start, end


def affordability_pressure(sources_dir) -> pd.DataFrame:
    """MAC-09: 12-month change in provincial CPI minus 12-month change in the provincial minimum wage, in points."""
    cpi = pd.read_csv(sources_dir / "cpi_allitems_2023_2026.csv")
    cpi["m"] = pd.PeriodIndex(cpi.ref_date, freq="M")
    mw = pd.read_csv(sources_dir / "minimum_wage_2022_2026.csv")
    mw["d"] = pd.to_datetime(mw.effective_date)
    rows = []
    for prov, name in PROVINCE_NAME.items():
        c = cpi[cpi.geo == name].set_index("m").value_2002_100
        w = mw[mw.province == name].sort_values("d")
        wage = lambda p: w[w.d <= p.to_timestamp(how="end")].general_minimum_wage_cad.iloc[-1]
        for p in c.index:
            if p - 12 in c.index:
                rows.append((prov, p, 100 * (c[p] / c[p - 12] - 1) - 100 * (wage(p) / wage(p - 12) - 1)))
    return pd.DataFrame(rows, columns=["province", "month", "pressure"])


# ---------------------------------------------------------------- stage 1: underlying demand

def ramp_factor(age_days: np.ndarray) -> np.ndarray:
    return np.interp(age_days / 365.25, RAMP_YEARS, RAMP_LEVELS)


def growth_index(dim_date: pd.DataFrame, comp: dict) -> pd.Series:
    """TR-01: linear in logs between fiscal-year midpoints through each year's growth; FY2026 average = 1."""
    d = dim_date.assign(d=pd.to_datetime(dim_date.date))
    years = sorted(comp)
    mids = {y: d[d.fiscal_year == y].d.mean() for y in years}
    knots_t, knots_v, level = [], [], 0.0
    for i, y in enumerate(years):
        if i:
            level += np.log1p(comp[y])
        knots_t.append(mids[y].value); knots_v.append(level)
    t = d.d.astype("int64").to_numpy()
    span = (mids[years[-1]] - mids[years[0]]).value / (len(years) - 1)
    first_slope, last_slope = np.log1p(comp[years[0]]) / span, np.log1p(comp[years[-1]]) / span
    v = np.interp(t, knots_t, knots_v)
    v = np.where(t < knots_t[0], knots_v[0] + (t - knots_t[0]) * first_slope, v)
    v = np.where(t > knots_t[-1], knots_v[-1] + (t - knots_t[-1]) * last_slope, v)
    g = pd.Series(np.exp(v), index=d.d.dt.date.to_numpy())
    return g / g[(d.fiscal_year == 2026).to_numpy()].mean()


def underlying(cfg, params: Params, tables: dict, sealed: Sealed) -> pd.DataFrame:
    """One row per store per day of its trading life in the history, with expected demand before holidays."""
    start, end = history_window(tables["dim_date"], cfg.history_last_fiscal_year, cfg.history_last_fiscal_quarter)
    dd = tables["dim_date"].assign(d=pd.to_datetime(tables["dim_date"].date).dt.date)
    dd = dd[(dd.d >= start) & (dd.d <= end)]
    stores = tables["dim_store"].assign(open_d=pd.to_datetime(tables["dim_store"].open_date).dt.date)
    stores = stores[stores.open_d <= end].sort_values("store_id")

    frames = []
    for _, s in stores.iterrows():
        days = dd[dd.d >= s.open_d]
        frames.append(pd.DataFrame({"date_id": days.date_id.to_numpy(), "date": days.d.to_numpy(),
                                    "fiscal_year": days.fiscal_year.to_numpy(), "fiscal_week": days.fiscal_week.to_numpy(),
                                    "weekday": days.day_of_week.to_numpy(), "store_id": s.store_id, "province": s.province,
                                    "market_id": s.market_id, "format": s.format, "open_date": s.open_d}))
    f = pd.concat(frames, ignore_index=True)
    f["month"] = pd.PeriodIndex(pd.to_datetime(f.date), freq="M")

    base = params.value("SE-07") * np.where(f.format == "compact", params.value("SE-04"), 1.0)
    level = f.store_id.map(sealed.level).to_numpy()
    age = (pd.to_datetime(f.date) - pd.to_datetime(f.open_date)).dt.days.to_numpy()
    ramp = ramp_factor(age)
    growth = f.date.map(growth_index(tables["dim_date"], sealed.comp_trx)).to_numpy()
    dow = f.weekday.map(params.vector("DS-03") * 7).to_numpy()
    season = pd.to_datetime(f.date).dt.month.map(_month_index(params)).to_numpy()
    press = affordability_pressure(cfg.calibration_sources).set_index(["province", "month"]).pressure
    pressure = pd.Series(list(zip(f.province, f.month))).map(press).to_numpy()
    if np.isnan(pressure).any():
        raise ValueError("Affordability pressure is missing for some province-months; check the CPI and wage files.")
    trade = 1 + sealed.trade_down * pressure / 100

    f["status"] = STATUS_OPEN
    event_mult = _events(f, sealed.events)
    remodel_mult = _remodels(f, sealed.remodel_lift)
    f["e_under"] = base * level * ramp * growth * dow * season * trade * event_mult * remodel_mult
    f.loc[f.status != STATUS_OPEN, "e_under"] = 0.0
    # Internal factors, kept for the checks (TR-01, TR-09); never published
    f["base"], f["level"], f["ramp"], f["growth"], f["dow"] = base, level, ramp, growth, dow
    f["season"], f["trade_down"], f["event_mult"], f["remodel_mult"] = season, trade, event_mult, remodel_mult
    f["e_core"] = base * level * growth
    return f


def _month_index(params: Params) -> dict:
    v = params.vector("DS-04")
    months = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                           "September", "October", "November", "December"], 1)}
    return {months.get(k, int(k) if str(k).isdigit() else None): x for k, x in v.items()}


def _events(f: pd.DataFrame, events: pd.DataFrame) -> np.ndarray:
    mult = np.ones(len(f))
    d = pd.to_datetime(f.date)
    for _, e in events.iterrows():
        stores = set(filter(None, e.stores.split(";")))
        on = f.store_id.isin(stores).to_numpy()
        start = pd.Timestamp(e.start_date)
        if e.type == COMPETITOR:
            end = pd.Timestamp(e.end_date)
            loss0, loss1 = float(e.initial_loss_pct) / 100, float(e.permanent_loss_pct) / 100
            frac = ((d - start) / (end - start)).clip(0, 1).to_numpy()
            loss = np.where(d >= start, loss0 + (loss1 - loss0) * frac, 0.0)
            mult = np.where(on, mult * (1 - loss), mult)
        elif e.type == LOCAL:
            end = pd.Timestamp(e.end_date)
            size = float(e.size_pct) / 100 * (1 if e.direction == "up" else -1)
            ease_start = end - pd.Timedelta(weeks=4) + pd.Timedelta(days=1)
            w = np.where((d >= start) & (d <= end), 1.0, 0.0)
            w = np.where((d >= ease_start) & (d <= end), ((end - d).dt.days + 1).to_numpy() / 28, w)
            mult = np.where(on, mult * (1 + size * w), mult)
        elif e.type == DISRUPTION:
            closed = on & (d >= start).to_numpy() & (d <= pd.Timestamp(e.end_date)).to_numpy()
            f.loc[closed, "status"] = STATUS_UNPLANNED
    return mult


def _remodels(f: pd.DataFrame, lifts: dict) -> np.ndarray:
    mult = np.ones(len(f))
    for store, (reopen, lift) in lifts.items():
        on = (f.store_id == store).to_numpy()
        closed = on & (f.date >= reopen - timedelta(days=REMODEL_CLOSED_DAYS)).to_numpy() & (f.date < reopen).to_numpy()
        f.loc[closed & (f.status == STATUS_OPEN).to_numpy(), "status"] = STATUS_REMODEL
        mult = np.where(on & (f.date >= reopen).to_numpy(), mult * (1 + lift), mult)
    return mult


# ---------------------------------------------------------------- stage 2 and 3: holidays and month neutrality

def apply_holidays(f: pd.DataFrame, params: Params, dim_holiday: pd.DataFrame, recapture: float) -> pd.DataFrame:
    """Holiday mechanics (CAL-03 to CAL-07, DS-12), then month neutrality (TR-02)."""
    h = dim_holiday.assign(d=pd.to_datetime(dim_holiday.date).dt.date).set_index(["province", "d"]).trading_status
    hs = pd.Series(list(zip(f.province, f.date))).map(h).fillna("open").to_numpy()
    f = f.copy()
    is_open = (f.status == STATUS_OPEN).to_numpy()
    f.loc[is_open & (hs == "closed"), "status"] = STATUS_HOLIDAY
    f.loc[is_open & (hs == "reduced hours"), "status"] = STATUS_REDUCED

    reduced, lift, split = params.value("CAL-03"), params.value("DS-12"), (0.6, 0.4)  # CAL-06
    e = f.e_under.to_numpy().copy()
    e[f.status.to_numpy() == STATUS_REDUCED] *= reduced
    e[f.status.to_numpy() == STATUS_HOLIDAY] = 0.0
    pre_inc, rec_inc = np.zeros(len(f)), np.zeros(len(f))
    status = f.status.to_numpy()
    for _, idx in f.groupby("store_id").indices.items():
        idx = np.sort(idx)
        trading = [i for i in idx if status[i] in (STATUS_OPEN, STATUS_REDUCED)]
        pos = {i: k for k, i in enumerate(idx)}
        for i in idx:
            if status[i] != STATUS_HOLIDAY:
                continue
            lost = f.e_under.iat[i]                               # CAL-04: the closed day's expected demand
            before = [j for j in trading if pos[j] < pos[i]]
            after = [j for j in trading if pos[j] > pos[i]]
            if before:
                rec_inc[before[-1]] += lost * recapture * split[0]
                pre_inc[before[-1]] = e[before[-1]] * (lift - 1)  # DS-12: the open day before the closure
            if after:
                rec_inc[after[0]] += lost * recapture * split[1]
    f["pre_increment"], f["recapture_increment"] = pre_inc, rec_inc
    f["e_holiday"] = e + np.maximum(pre_inc, rec_inc)           # CAL-07: the larger increment only

    totals = f.groupby(["store_id", "month"])[["e_under", "e_holiday"]].transform("sum")
    scale = np.where(totals.e_holiday > 0, totals.e_under / totals.e_holiday.replace(0, np.nan), 1.0)
    f["expected"] = f.e_holiday * np.nan_to_num(scale, nan=1.0)
    return f


# ---------------------------------------------------------------- stage 4: noise

def drift_settings(params: Params) -> tuple[float, float]:
    return params.value("TR-06a"), params.value("TR-06b")


def apply_noise(f: pd.DataFrame, seed: int, sd: float, phi: float) -> pd.DataFrame:
    """TR-06: AR(1) store drift by fiscal week on the log level; TR-07: Poisson count for the day."""
    f = f.copy()
    week = f.fiscal_year.astype(int) * 100 + f.fiscal_week.astype(int)
    rng = stream(seed, "traffic_drift")
    innov = sd * np.sqrt(1 - phi ** 2)
    drift = {}
    for store in sorted(f.store_id.unique()):
        weeks = sorted(week[f.store_id == store].unique())
        x = rng.normal(0, sd)
        for k, w in enumerate(weeks):
            if k:
                x = phi * x + rng.normal(0, innov)
            drift[(store, w)] = np.exp(x - sd ** 2 / 2)
    f["drift"] = [drift[k] for k in zip(f.store_id, week)]
    lam = f.expected.to_numpy() * f.drift.to_numpy()
    f["transactions"] = stream(seed, "traffic_counts").poisson(lam).astype(np.int64)
    return f


# ---------------------------------------------------------------- the published table

def build_traffic(cfg, params: Params, tables: dict, seed_hex: str, sealed_bytes: bytes,
                  keep_components: bool = False) -> pd.DataFrame:
    sealed = read_sealed(sealed_bytes)
    f = underlying(cfg, params, tables, sealed)
    f = apply_holidays(f, params, tables["dim_holiday"], sealed.recapture)
    f = apply_noise(f, seed_from_hex(seed_hex), *drift_settings(params))
    if keep_components:
        return f
    out = f[["date_id", "date", "store_id", "status", "transactions"]].rename(columns={"status": "trading_status"})
    return out.sort_values(["store_id", "date_id"]).reset_index(drop=True)


# ---------------------------------------------------------------- the noise measure (same method as m5_patterns.ipynb)

def weekly_noise(f: pd.DataFrame, dim_store: pd.DataFrame, events: pd.DataFrame, calendar_adjusted: bool = True) -> pd.DataFrame:
    """Store-total weekly noise and persistence on mature comparable stores and eligible full weeks.

    Same measure as the M5 notebook: weekly totals against a 13-week centred moving average, in logs.
    A week counts only if the store is mature (open three years or more) for the whole week, the week has no
    closure or reduced-hours day, and no remodel, unplanned closure or store-level event falls inside its
    13-week window.
    """
    g = f.assign(wk=f.fiscal_year.astype(int) * 100 + f.fiscal_week.astype(int))
    rows = []
    for store, s in g.groupby("store_id"):
        wk = s.groupby("wk").agg(trx=("transactions", "sum"), exp=("expected", "sum"), days=("date", "size"), first=("date", "min"), last=("date", "max"),
                                 closed=("status", lambda x: (x != STATUS_OPEN).sum()),
                                 structural=("status", lambda x: x.isin([STATUS_REMODEL, STATUS_UNPLANNED]).sum()),
                                 ramp=("ramp", "min"))
        wk = wk[wk.days == 7]
        wk["y"] = wk.trx / wk.exp if calendar_adjusted else wk.trx
        struct = wk.structural.astype(bool).copy()
        for _, e in events.iterrows():
            if store in e.stores.split(";") and e.type in (COMPETITOR, LOCAL):
                active = (pd.to_datetime(wk["last"]) >= pd.Timestamp(e.start_date)) & \
                         (pd.to_datetime(wk["first"]) <= pd.Timestamp(e.end_date))
                struct |= active.to_numpy()
        with np.errstate(divide="ignore", invalid="ignore"):
            dev = np.log(wk.y.astype(float) / wk.y.astype(float).rolling(13, center=True).mean())
        window_struct = struct.astype(int).rolling(13, center=True, min_periods=1).max().astype(bool)
        ok = (wk.ramp >= 1.0) & (wk.closed == 0) & ~window_struct
        dev = dev.where(ok)
        if dev.notna().sum() >= 52:
            rows.append({"store_id": store, "noise_sd": dev.std(), "lag1_autocorr": dev.autocorr(1),
                         "weeks": int(dev.notna().sum())})
    return pd.DataFrame(rows)
