"""Milestone 3 validation on the real sealed world.

Runs only on the machine that holds the private seed and sealed file; skipped everywhere
else. The checks report pass or fail and never print a sealed value.
"""
import numpy as np
import pytest

from kettlerock_engine import traffic as T
from kettlerock_engine.seal import SEED_FILE, SEALED_FILE, verify_seal


@pytest.fixture(scope="module")
def real(cfg, params, tables):
    if not (cfg.sealed_dir / SEALED_FILE).exists():
        pytest.skip("No sealed file on this machine")
    verify_seal(cfg)
    seed = (cfg.sealed_dir / SEED_FILE).read_text(encoding="ascii").strip()
    sealed_bytes = (cfg.sealed_dir / SEALED_FILE).read_bytes()
    f = T.build_traffic(cfg, params, tables, seed, sealed_bytes, keep_components=True)
    return f, T.read_sealed(sealed_bytes)


def test_real_month_neutrality(real):
    f, _ = real
    m = f.groupby(["store_id", "month"])[["e_under", "expected"]].sum()
    assert np.allclose(m.e_under, m.expected, rtol=1e-12, atol=1e-6)


def test_real_normalised_baseline(real, params):
    f, _ = real
    m = f[(f.fiscal_year == 2026) & (f.ramp >= 1) & (f.format == "standard") & (f.status == T.STATUS_OPEN)]
    norm = m.e_under / (m.level * m.growth * m.dow * m.season * m.trade_down * m.event_mult * m.remodel_mult)
    assert np.allclose(norm, params.value("SE-07"), rtol=1e-12)


def test_real_noise_and_persistence(real, tables, params):
    f, s = real
    n = T.weekly_noise(f, tables["dim_store"], s.events, calendar_adjusted=True)
    lo, hi = params.bounds("VAR-06")
    assert lo <= n.noise_sd.median() <= hi, "store-total weekly noise outside VAR-06"
    lo, hi = params.bounds("VAR-07")
    assert lo <= n.lag1_autocorr.median() <= hi, "store-total weekly persistence outside VAR-07"


def test_real_store_strength_distribution(real):
    f, s = real
    lv = np.log([s.level[x] for x in f.store_id.unique()])
    assert len(lv) == 40
    assert 0.13 <= lv.std() <= 0.27 and 0.90 <= np.exp(lv).mean() <= 1.10
