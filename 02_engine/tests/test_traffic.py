"""Milestone 3: daily traffic. Built from a public test seed, never the private one."""
from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

from kettlerock_engine import traffic as T
from kettlerock_engine.traffic import (STATUS_OPEN, STATUS_REDUCED, STATUS_HOLIDAY, STATUS_REMODEL,
                                       STATUS_UNPLANNED)
from conftest import TEST_SEED

CLOSED = {STATUS_HOLIDAY, STATUS_REMODEL, STATUS_UNPLANNED}


@pytest.fixture(scope="module")
def f(traffic_components):
    return traffic_components


@pytest.fixture(scope="module")
def sealed(test_sealed_bytes):
    return T.read_sealed(test_sealed_bytes)


@pytest.fixture(scope="module")
def window(cfg, tables):
    return T.history_window(tables["dim_date"], cfg.history_last_fiscal_year, cfg.history_last_fiscal_quarter)


# ---------------------------------------------------------------- grain and statuses

def test_history_runs_from_fy2025_to_q3_fy2027_close(window):
    assert str(window[0]) == "2024-02-04" and str(window[1]) == "2026-10-31"


def test_one_row_per_store_day_from_opening(traffic_table, tables, window):
    start, end = window
    s = tables["dim_store"].assign(o=pd.to_datetime(tables["dim_store"].open_date).dt.date)
    s = s[s.o <= end]
    assert len(s) == 40, "the two planned stores open after the history ends"
    expected_rows = sum((end - max(o, start)).days + 1 for o in s.o)
    assert len(traffic_table) == expected_rows
    assert not traffic_table.duplicated(["store_id", "date_id"]).any()
    assert set(traffic_table.store_id) == set(s.store_id)


def test_published_columns_only(traffic_table):
    assert list(traffic_table.columns) == ["date_id", "date", "store_id", "trading_status", "transactions"]


def test_counts_are_whole_and_closed_days_are_zero(traffic_table):
    assert traffic_table.transactions.dtype.kind == "i" and (traffic_table.transactions >= 0).all()
    assert (traffic_table[traffic_table.trading_status.isin(CLOSED)].transactions == 0).all()
    assert (traffic_table[traffic_table.trading_status == STATUS_OPEN].transactions > 0).all()


def test_holiday_statuses_follow_provincial_law(f, tables):
    h = tables["dim_holiday"].assign(d=pd.to_datetime(tables["dim_holiday"].date).dt.date)
    h = h.set_index(["province", "d"]).trading_status
    law = pd.Series(list(zip(f.province, f.date))).map(h).fillna("open").to_numpy()
    normal = ~f.status.isin([STATUS_REMODEL, STATUS_UNPLANNED]).to_numpy()
    assert (f.status.to_numpy()[normal & (law == "closed")] == STATUS_HOLIDAY).all()
    assert (f.status.to_numpy()[normal & (law == "reduced hours")] == STATUS_REDUCED).all()
    assert (law[f.status.to_numpy() == STATUS_HOLIDAY] == "closed").all()


def test_remodel_closes_seven_days_before_reopening(f, sealed):
    for store, (reopen, _) in sealed.remodel_lift.items():
        closed = f[(f.store_id == store) & (f.status == STATUS_REMODEL)].date
        if len(closed):
            assert sorted(closed) == [reopen - timedelta(days=k) for k in range(7, 0, -1)]


def test_unplanned_closures_match_disruption_events(f, sealed):
    ev = sealed.events[sealed.events.type == "store_disruption"]
    want = set()
    for _, e in ev.iterrows():
        d0, d1 = pd.Timestamp(e.start_date).date(), pd.Timestamp(e.end_date).date()
        want |= {(e.stores, d0 + timedelta(days=k)) for k in range((d1 - d0).days + 1)}
    got = set(zip(f[f.status == STATUS_UNPLANNED].store_id, f[f.status == STATUS_UNPLANNED].date))
    assert got == {w for w in want if w in set(zip(f.store_id, f.date))}


# ---------------------------------------------------------------- holiday mechanics

def test_month_neutrality_on_expected_values(f):
    m = f.groupby(["store_id", "month"])[["e_under", "expected"]].sum()
    assert np.allclose(m.e_under, m.expected, rtol=1e-12, atol=1e-6)


def test_larger_of_rule(f, params):
    base = f.e_under * np.where(f.status == STATUS_REDUCED, params.value("CAL-03"), 1.0)
    base = base.where(f.status != STATUS_HOLIDAY, 0.0)
    added = f.e_holiday - base
    assert np.allclose(added, np.maximum(f.pre_increment, f.recapture_increment))
    assert (f.pre_increment[f.recapture_increment > 0] >= 0).all()


def test_recapture_only_next_to_holiday_closures(f):
    for store, s in f.groupby("store_id"):
        s = s.sort_values("date").reset_index(drop=True)
        for i in s.index[s.recapture_increment > 0]:
            closed_neighbours = []
            for step in (-1, 1):
                j = i + step
                while 0 <= j < len(s) and s.status[j] in CLOSED:
                    closed_neighbours.append(s.status[j]); j += step
            assert STATUS_HOLIDAY in closed_neighbours


def test_no_recapture_after_remodel_or_unplanned_closure(f):
    for store, s in f.groupby("store_id"):
        s = s.sort_values("date").reset_index(drop=True)
        for i in s.index[s.status.isin([STATUS_REMODEL, STATUS_UNPLANNED])]:
            for j in (i - 1, i + 1):
                if 0 <= j < len(s) and s.status[j] in (STATUS_OPEN, STATUS_REDUCED):
                    holiday_near = s.status[max(0, j - 3):j + 4].eq(STATUS_HOLIDAY).any()
                    if not holiday_near:
                        assert s.recapture_increment[j] == 0


# ---------------------------------------------------------------- levels and shapes

def test_normalised_baseline_is_705(f, sealed, params):
    """TR-09: mature standard, event-free stores in FY2026."""
    event_stores = set(";".join(sealed.events.stores).split(";"))
    m = f[(f.fiscal_year == 2026) & (f.ramp >= 1) & (f.format == "standard") & (f.status == STATUS_OPEN)
          & (f.remodel_mult == 1) & (f.event_mult == 1) & ~f.store_id.isin(event_stores)]
    assert m.store_id.nunique() >= 10
    norm = m.e_under / (m.level * m.growth * m.dow * m.season * m.trade_down)
    assert norm.mean() == pytest.approx(params.value("SE-07"), rel=1e-9)
    # The underlying level over the whole of FY2026, for every store trading all year, is exactly 705
    core = f[f.fiscal_year == 2026]
    full_year = core.groupby("store_id").date.transform("size") == core.date.nunique()
    core = core[full_year]
    per_store = (core.e_core / core.level / np.where(core.format == "compact", params.value("SE-04"), 1)).groupby(core.store_id).mean()
    assert np.allclose(per_store, params.value("SE-07"), rtol=1e-12)


def test_ramp_yearly_averages(f, params):
    age = (pd.to_datetime(f.date) - pd.to_datetime(f.open_date)).dt.days / 365.25
    for y, pid in enumerate(["SE-05a", "SE-05b", "SE-05c"]):
        days = np.arange(0, 366) / 365.25 + y
        assert T.ramp_factor(days * 365.25).mean() == pytest.approx(params.value(pid), abs=0.01)
        sel = (age >= y) & (age < y + 1)
        if sel.sum() > 300:
            assert f.ramp[sel].mean() == pytest.approx(params.value(pid), abs=0.01)


def test_day_of_week_shares(traffic_table, f, params):
    g = f[f.status == STATUS_OPEN].assign(wk=f.fiscal_year * 100 + f.fiscal_week)
    g = g[g.groupby(["store_id", "wk"]).date.transform("size") == 7]
    share = (g.transactions / g.groupby(["store_id", "wk"]).transactions.transform("sum")).groupby(g.weekday).mean()
    assert (share - params.vector("DS-03")).abs().max() < 0.005


def test_month_shape_follows_ds04(f, params):
    m = f[(f.ramp >= 1) & (f.event_mult == 1) & (f.remodel_mult == 1)]
    idx = (m.e_under / (m.level * m.growth * m.dow * m.trade_down)).groupby(pd.to_datetime(m.date).dt.month).mean()
    target = pd.Series(T._month_index(params))
    assert np.corrcoef(idx.sort_index(), target.sort_index())[0, 1] > 0.999


def test_store_strength_distribution(f, sealed):
    lv = np.log(pd.Series({s: sealed.level[s] for s in f.store_id.unique()}))
    assert len(lv) == 40
    assert 0.13 <= lv.std() <= 0.27, "range across 100 test seeds was 0.138 to 0.265"
    assert 0.90 <= np.exp(lv).mean() <= 1.10, "range across 100 test seeds was 0.905 to 1.060"


# ---------------------------------------------------------------- noise (TR-08) and reproducibility

def test_noise_and_persistence_in_bands(f, tables, sealed, params):
    n = T.weekly_noise(f, tables["dim_store"], sealed.events, calendar_adjusted=True)
    assert len(n) >= 15
    lo, hi = params.bounds("VAR-06")
    assert lo <= n.noise_sd.median() <= hi
    lo, hi = params.bounds("VAR-07")
    assert lo <= n.lag1_autocorr.median() <= hi


def test_noise_measure_isolates_randomness(cfg, params, tables, test_sealed_bytes):
    """With the drift switched off, the calendar-adjusted measure sees only Poisson variation."""
    s = T.read_sealed(test_sealed_bytes)
    g = T.apply_holidays(T.underlying(cfg, params, tables, s), params, tables["dim_holiday"], s.recapture)
    g = T.apply_noise(g, int(TEST_SEED, 16), 1e-12, 0.0)
    n = T.weekly_noise(g, tables["dim_store"], s.events, calendar_adjusted=True)
    assert n.noise_sd.median() < 0.02


def test_same_seed_same_table(cfg, params, tables, test_sealed_bytes, traffic_table):
    again = T.build_traffic(cfg, params, tables, TEST_SEED, test_sealed_bytes)
    assert again.to_csv(index=False) == traffic_table.to_csv(index=False)


def test_code_constants_match_parameter_text(params):
    assert "0.60 at opening, 0.80 at one year, 0.90 at two years and 1.00 at three years" in params.row("TR-03")["central_value"]
    assert params.value("TR-04") == T.REMODEL_CLOSED_DAYS
    assert "longer than 14 consecutive days" in params.row("CMP-01")["central_value"]


def test_history_refuses_without_a_seal(cfg, params, tables, tmp_path):
    import dataclasses
    from kettlerock_engine.build import build_history
    bare = dataclasses.replace(cfg, sealed_dir=tmp_path / "s", commitment_dir=tmp_path / "c")
    with pytest.raises(FileNotFoundError):
        build_history(bare, params, tables)
