"""Fiscal calendar and closures match specification sections 7 and 9."""
import pandas as pd
import pytest

SPEC_YEARS = {  # fiscal year: (start, end, weeks), from the section 7 table
    2025: ("2024-02-04", "2025-02-01", 52), 2026: ("2025-02-02", "2026-01-31", 52),
    2027: ("2026-02-01", "2027-01-30", 52), 2028: ("2027-01-31", "2028-01-29", 52),
    2029: ("2028-01-30", "2029-02-03", 53),
}


@pytest.mark.parametrize("fy,expected", SPEC_YEARS.items())
def test_fiscal_year_bounds(tables, fy, expected):
    d = tables["dim_date"][tables["dim_date"].fiscal_year == fy]
    assert (d.date.min(), d.date.max(), d.fiscal_week.max()) == expected


def test_years_start_sunday_end_saturday(tables):
    d = tables["dim_date"]
    g = d.groupby("fiscal_year")
    assert (d.loc[g.date.idxmin(), "day_of_week"] == "Sunday").all()
    assert (d.loc[g.date.idxmax(), "day_of_week"] == "Saturday").all()


def test_quarter_ends_fy2027(tables):
    d = tables["dim_date"][tables["dim_date"].fiscal_year == 2027]
    ends = d.groupby("fiscal_quarter").date.max().tolist()
    assert ends[:3] == ["2026-05-02", "2026-08-01", "2026-10-31"]


def test_454_pattern(tables):
    d = tables["dim_date"]
    weeks = d[d.is_53_week_year == 0].groupby(["fiscal_year", "fiscal_month"]).fiscal_week.nunique()
    assert set(weeks.groupby(level=0).apply(lambda s: tuple(s)).tolist()) == {(4, 5, 4) * 4}
    w53 = d[d.is_53_week_year == 1].groupby("fiscal_month").fiscal_week.nunique()
    assert w53.loc[12] == 5 and w53.sum() == 53


def test_only_fy2029_has_53_weeks(tables):
    flags = tables["dim_date"].groupby("fiscal_year").is_53_week_year.max()
    assert flags[flags == 1].index.tolist() == [2029]


def test_christmas_closed_everywhere(tables):
    h = tables["dim_holiday"]
    xmas = h[h.holiday_key == "christmas_day"]
    assert (xmas.trading_status == "closed").all() and xmas.province.nunique() == 4


def test_boxing_day_by_province(tables):
    h = tables["dim_holiday"]
    b = h[h.holiday_key == "boxing_day"].groupby("province").trading_status.first().to_dict()
    assert b == {"ON": "open", "QC": "reduced hours", "NS": "closed", "NB": "closed"}


def test_known_dates(tables):
    h = tables["dim_holiday"].set_index(["holiday_key", "calendar_year", "province"]).date
    assert h[("easter_sunday", 2026, "ON")] == "2026-04-05"
    assert h[("good_friday", 2025, "ON")] == "2025-04-18"
    assert h[("victoria_day", 2026, "ON")] == "2026-05-18"
    assert h[("thanksgiving_day", 2026, "ON")] == "2026-10-12"
    assert h[("canada_day", 2029, "ON")] == "2029-07-02"     # July 1, 2029 is a Sunday
    assert h[("canada_day", 2029, "QC")] == "2029-07-01"


def test_remembrance_day_only_atlantic(tables):
    h = tables["dim_holiday"]
    r = h[(h.holiday_key == "remembrance_day") & (h.trading_status == "closed")]
    assert set(r.province) == {"NS", "NB"}
