"""Milestone 2: the sealed world.

These tests use a public test seed, never the private one. They read the sealed file
as plain text and check every rule independently of the code that drew it.
"""
import csv
import dataclasses
import io
from datetime import date, timedelta

import pandas as pd
import pytest

from kettlerock_engine import world, seal

TEST_SEED = "0123456789abcdef" * 4
COMMIT = "a" * 40


@pytest.fixture(scope="module")
def sealed_bytes(params, tables):
    return world.draw_world(TEST_SEED, params, tables)


@pytest.fixture(scope="module")
def sealed(sealed_bytes):
    return pd.read_csv(io.BytesIO(sealed_bytes), dtype=str, keep_default_na=False)


@pytest.fixture(scope="module")
def events(sealed):
    ev = sealed[sealed.record_type == "event"].pivot(index="scope", columns="field", values="value")
    ev["start"] = pd.to_datetime(ev.start_date).dt.date
    ev["end"] = pd.to_datetime(ev.end_date.replace("", None)).dt.date
    return ev


@pytest.fixture(scope="module")
def quarter_of(tables):
    dd = tables["dim_date"].assign(d=lambda x: pd.to_datetime(x.date).dt.date).set_index("d")
    return lambda d: (int(dd.at[d, "fiscal_year"]), int(dd.at[d, "fiscal_quarter"]))


# ---------------------------------------------------------------- canonical bytes

def test_same_seed_same_bytes(params, tables, sealed_bytes):
    assert world.draw_world(TEST_SEED, params, tables) == sealed_bytes


def test_different_seed_different_world(params, tables, sealed_bytes):
    assert world.draw_world("f" * 64, params, tables) != sealed_bytes


def test_canonical_format(sealed_bytes):
    text = sealed_bytes.decode("utf-8")
    assert "\r" not in text and text.endswith("\n")
    rows = list(csv.reader(io.StringIO(text)))
    assert rows[0] == world.SEALED_COLUMNS
    body = [tuple(r[:4]) for r in rows[1:]]
    assert body == sorted(body), "rows must be sorted"
    assert len(set(body)) == len(body), "no duplicate keys"


def test_numbers_have_fixed_decimals(sealed):
    numeric = sealed[sealed.value.str.fullmatch(r"-?\d+\.\d+")]
    assert len(numeric) > 0
    assert numeric.value.str.split(".").str[1].str.len().eq(world.DECIMALS).all()


def test_seed_must_be_256_bits():
    with pytest.raises(ValueError):
        world.seed_from_hex("1234")


# ---------------------------------------------------------------- parameter draws

def _values(sealed, sid):
    return sealed[(sealed.record_type == "parameter") & (sealed.sealed_parameter_id == sid)].value.astype(float)


@pytest.mark.parametrize("pid,sid", [("SE-19", "SWP-REMODEL-LIFT"), ("PR-01", "SWP-PRICE-CONSUMABLES"),
                                     ("PR-02", "SWP-PRICE-GENERAL"), ("PR-03", "SWP-PRICE-SEASONAL"),
                                     ("PR-06", "SWP-PRICE-TRAFFIC"), ("CAL-05", "SWP-RECAPTURE"),
                                     ("GR-01", "SWP-COMP-TRX"), ("GR-02", "SWP-COMP-TKT"),
                                     ("MAC-10", "SWP-TRADE-DOWN")])
def test_draws_inside_parameter_range(params, sealed, pid, sid):
    lo, hi = params.bounds(pid)
    v = _values(sealed, sid)
    assert len(v) > 0 and v.between(lo, hi).all()


def test_one_draw_per_item_store_remodel_and_year(sealed, tables):
    s = sealed[sealed.record_type == "parameter"]
    prices = s[s.sealed_parameter_id.str.startswith("SWP-PRICE-") & (s.field == "price_response")]
    assert sorted(prices.scope) == sorted(tables["dim_product"].product_id)
    assert sorted(s[s.sealed_parameter_id == "SWP-STORE-LEVEL"].scope) == sorted(tables["dim_store"].store_id)
    remodels = tables["dim_store"].remodel_reopen_date.dropna()
    assert len(s[s.sealed_parameter_id == "SWP-REMODEL-LIFT"]) == len(remodels[remodels.astype(str) != ""])
    assert sorted(s[s.sealed_parameter_id == "SWP-COMP-TRX"].scope) == ["FY2025", "FY2026", "FY2027"]


def test_store_level_factors_average_near_one(sealed):
    assert abs(_values(sealed, "SWP-STORE-LEVEL").mean() - 1) < 0.15


# ---------------------------------------------------------------- hidden events (rules EV-01 to EV-16)

def test_event_count_and_types(events, params):
    lo, hi = params.bounds("EV-01")
    assert lo <= len(events) <= hi
    types = list(events.type)
    assert types.count(world.COMPETITOR) == 1 and types.count(world.SUPPLIER) == 1
    assert len(set(types)) == len(types), "remaining types are drawn without replacement"


def test_event_timing_and_coverage(events, quarter_of):
    for _, e in events.iterrows():
        assert date(2024, 2, 4) <= e.start <= date(2026, 9, 5)
        if e.type != world.SEASONAL:
            assert e.start.weekday() == 6, "events start on a Sunday"
    assert {2025, 2026, 2027} <= {quarter_of(d)[0] for d in events.start}
    assert pd.Series([quarter_of(d) for d in events.start]).value_counts().max() <= 2


def _occupancy_end(e):
    if e.type == world.SUPPLIER:
        return e.start + timedelta(weeks=13) - timedelta(days=1)
    return e.end


def test_severe_events_never_overlap(events):
    severe = sorted((e.start, _occupancy_end(e)) for _, e in events.iterrows()
                    if e.type in {world.COMPETITOR, world.SUPPLIER, world.FREIGHT, world.SEASONAL})
    for a, b in zip(severe, severe[1:]):
        assert b[0] > a[1]


def test_store_and_market_spacing(events):
    local = [e for _, e in events.iterrows() if e.type in {world.COMPETITOR, world.LOCAL, world.DISRUPTION}]
    for i, a in enumerate(local):
        for b in local[i + 1:]:
            if a.market_id == b.market_id:
                assert abs((a.start - b.start).days) >= 365
            if set(a.stores.split(";")) & set(b.stores.split(";")):
                assert a.end < b.start or b.end < a.start


def test_event_sizes_and_durations(events, params):
    for _, e in events.iterrows():
        if e.type == world.COMPETITOR:
            loss, perm = float(e.initial_loss_pct), float(e.permanent_loss_pct)
            assert params.bounds("EV-02")[0] <= loss <= params.bounds("EV-02")[1]
            assert perm == pytest.approx(loss * params.value("EV-13"), abs=1e-9)
            assert params.bounds("EV-03")[0] <= float(e.recovery_months) <= params.bounds("EV-03")[1]
        if e.type == world.FREIGHT:
            assert params.bounds("EV-15")[0] <= int(e.duration_weeks) <= params.bounds("EV-15")[1]
        if e.type == world.LOCAL:
            assert params.bounds("EV-14")[0] <= int(e.duration_weeks) <= params.bounds("EV-14")[1]
        if e.type == world.DISRUPTION:
            assert params.bounds("EV-08")[0] <= int(e.closed_days) <= params.bounds("EV-08")[1]
        if e.type == world.SUPPLIER:
            assert e.end_date == "", "a supplier cost increase is permanent"


def test_events_only_hit_open_stores(events, tables):
    opened = dict(zip(tables["dim_store"].store_id, pd.to_datetime(tables["dim_store"].open_date).dt.date))
    for _, e in events.iterrows():
        for s in filter(None, e.stores.split(";")):
            assert opened[s] <= e.start


def test_rules_hold_across_many_seeds(params, tables, quarter_of):
    for i in range(40):
        ev = world.draw_events(world.seed_from_hex(f"{i:064x}"), params, tables)
        assert world.check_rules(ev, quarter_of) == []


def test_code_constants_match_parameter_text(params):
    assert "2024-02-04" in params.row("EV-11")["central_value"]
    assert "2026-09-05" in params.row("EV-11")["central_value"]
    assert "first 13 weeks" in params.row("EV-10")["central_value"]
    assert "10,000" in params.row("EV-16")["central_value"]
    assert "within 12 months" in params.row("EV-09")["central_value"]
    assert "at most two events start" in params.row("EV-09")["central_value"]


# ---------------------------------------------------------------- sealing and verification

@pytest.fixture()
def tmp_cfg(cfg, tmp_path):
    return dataclasses.replace(cfg, sealed_dir=tmp_path / "sealed", commitment_dir=tmp_path / "commitment")


def test_seal_then_verify(tmp_cfg):
    m = seal.seal(COMMIT, tmp_cfg)
    assert len(m["seed_sha256"]) == 64 and m["seed_sha256"] != m["sealed_world_sha256"]
    assert seal.verify_seal(tmp_cfg)["git_commit"] == COMMIT
    seed = (tmp_cfg.sealed_dir / "seed.txt").read_text()
    assert len(seed.strip()) == 64 and seed.endswith("\n")


def test_commit_sha_required(tmp_cfg):
    with pytest.raises(ValueError):
        seal.seal("main", tmp_cfg)


def test_seal_never_overwritten(tmp_cfg):
    seal.seal(COMMIT, tmp_cfg)
    with pytest.raises(RuntimeError):
        seal.seal(COMMIT, tmp_cfg)
    with pytest.raises(ValueError):
        seal.seal(COMMIT, tmp_cfg, replace=True, reason="")


def test_replacement_keeps_old_files_and_records_reason(tmp_cfg):
    first = seal.seal(COMMIT, tmp_cfg)
    second = seal.seal("b" * 40, tmp_cfg, replace=True, reason="test correction")
    assert (tmp_cfg.sealed_dir / "v1" / "sealed_world.csv").exists()
    ledger = list(csv.DictReader(open(tmp_cfg.commitment_dir / "commitments.csv", encoding="utf-8")))
    assert [r["status"] for r in ledger] == ["replaced", "active"]
    assert ledger[0]["replaced_reason"] == "test correction"
    assert first["seed_sha256"] != second["seed_sha256"]
    seal.verify_seal(tmp_cfg)


def test_verify_detects_a_changed_sealed_file(tmp_cfg):
    seal.seal(COMMIT, tmp_cfg)
    p = tmp_cfg.sealed_dir / "sealed_world.csv"
    p.write_bytes(p.read_bytes().replace(b"\n", b"\n ", 1))
    with pytest.raises(RuntimeError, match="does not match"):
        seal.verify_seal(tmp_cfg)


def test_harmless_input_change_is_a_warning(tmp_cfg, tmp_path):
    seal.seal(COMMIT, tmp_cfg)
    changed = tmp_path / "calibrated_parameters.csv"
    changed.write_bytes(tmp_cfg.calibrated_parameters.read_bytes() + b"\n")
    m = seal.verify_seal(dataclasses.replace(tmp_cfg, calibrated_parameters=changed))
    assert any("changed since sealing" in w for w in m["warnings"])


def test_input_change_that_moves_a_sealed_draw_fails(tmp_cfg, tmp_path):
    seal.seal(COMMIT, tmp_cfg)
    p = pd.read_csv(tmp_cfg.calibrated_parameters, dtype=str, keep_default_na=False)
    p.loc[p.parameter_id == "SE-19", "upper_bound"] = "9.00"
    changed = tmp_path / "calibrated_parameters.csv"
    p.to_csv(changed, index=False, lineterminator="\n")
    with pytest.raises(RuntimeError, match="does not reproduce"):
        seal.verify_seal(dataclasses.replace(tmp_cfg, calibrated_parameters=changed))


def test_commitment_files_hold_no_sealed_values(tmp_cfg):
    seal.seal(COMMIT, tmp_cfg)
    sealed = pd.read_csv(tmp_cfg.sealed_dir / "sealed_world.csv", dtype=str, keep_default_na=False)
    secrets_ = set(sealed.value[sealed.value.str.fullmatch(r"-?\d+\.\d{10}")])
    public = "".join(p.read_text(encoding="utf-8") for p in tmp_cfg.commitment_dir.iterdir())
    assert not any(v in public for v in secrets_)
    assert "SWP-" not in public
