"""Milestone 1: fiscal calendar (dim_date) and provincial holidays and closures (dim_holiday).

Fiscal years end on the Saturday closest to January 31 and are named by the calendar
year they end in. Weeks run Sunday to Saturday; quarters have 13 weeks split 4-5-4;
the extra week of a 53-week year goes to the final fiscal month.
"""
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

FISCAL_MONTH_NAMES = ["Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def fiscal_year_end(fy: int) -> date:
    """Saturday closest to January 31 of calendar year fy."""
    jan31 = date(fy, 1, 31)
    ahead = (5 - jan31.weekday()) % 7          # days forward to the next Saturday
    return jan31 + timedelta(ahead) if ahead <= 3 else jan31 - timedelta(7 - ahead)


def fiscal_year_start(fy: int) -> date:
    return fiscal_year_end(fy - 1) + timedelta(1)


def _month_in_quarter(week_in_quarter: int) -> int:
    return 1 if week_in_quarter <= 4 else (2 if week_in_quarter <= 9 else 3)


def build_dim_date(first_fy: int, last_fy: int) -> pd.DataFrame:
    rows = []
    for fy in range(first_fy, last_fy + 1):
        start, end = fiscal_year_start(fy), fiscal_year_end(fy)
        n_days = (end - start).days + 1
        is_53 = n_days == 371
        for i in range(n_days):
            d = start + timedelta(i)
            week = i // 7 + 1
            if week == 53:
                quarter, month = 4, 12
            else:
                quarter = (week - 1) // 13 + 1
                month = (quarter - 1) * 3 + _month_in_quarter((week - 1) % 13 + 1)
            rows.append({
                "date_id": int(d.strftime("%Y%m%d")), "date": d.isoformat(),
                "day_of_week": WEEKDAYS[d.weekday()], "day_of_week_num": (d.weekday() + 1) % 7 + 1,  # Sunday = 1
                "fiscal_year": fy, "fiscal_quarter": quarter, "fiscal_month": month,
                "fiscal_month_name": FISCAL_MONTH_NAMES[month - 1], "fiscal_week": week,
                "fiscal_day_of_year": i + 1, "is_53_week_year": int(is_53),
                "calendar_year": d.year, "calendar_month": d.month,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- holidays

def easter_sunday(year: int) -> date:
    """Anonymous Gregorian algorithm."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return date(year, month, day)


def resolve_date_rule(rule: str, year: int) -> date:
    kind, _, arg = rule.partition(":")
    if kind == "fixed":
        mm, dd = (int(x) for x in arg.split("-"))
        return date(year, mm, dd)
    if kind == "easter":
        return easter_sunday(year) + timedelta(int(arg))
    if kind == "nth_weekday":                       # nth_weekday:MM:MON:n
        mm, _, n = arg.split(":")
        first = date(year, int(mm), 1)
        offset = (0 - first.weekday()) % 7           # Monday = 0
        return first + timedelta(offset + 7 * (int(n) - 1))
    if kind == "monday_before":                     # last Monday strictly before MM-DD
        mm, dd = (int(x) for x in arg.split("-"))
        d = date(year, mm, dd) - timedelta(1)
        return d - timedelta(d.weekday())
    raise ValueError(f"Unknown date rule {rule}")


def build_dim_holiday(structure_dir: Path, first_fy: int, last_fy: int) -> pd.DataFrame:
    rules = pd.read_csv(structure_dir / "closure_rules.csv")
    legal = pd.read_csv(structure_dir / "legal_basis.csv").set_index("province")
    lo, hi = fiscal_year_start(first_fy), fiscal_year_end(last_fy)
    rows = []
    for year in range(lo.year, hi.year + 1):
        for _, r in rules.iterrows():
            base = resolve_date_rule(r["date_rule"], year)
            for prov in ["ON", "QC", "NS", "NB"]:
                d = base
                if prov == "ON" and r["holiday_key"] == "canada_day" and d.weekday() == 6:
                    d = d + timedelta(1)             # Ontario: closure moves to the Monday
                if not (lo <= d <= hi):
                    continue
                name = "Heritage Day" if (r["holiday_key"] == "family_day" and prov == "NS") else (
                    "Family Day" if r["holiday_key"] == "family_day" else r["holiday_name"])
                status = r[prov]
                rows.append({
                    "holiday_id": f"{d:%Y%m%d}-{prov}-{r['holiday_key']}", "date": d.isoformat(),
                    "calendar_year": d.year, "province": prov, "holiday_key": r["holiday_key"],
                    "holiday_name": name, "trading_status": status,
                    "legal_basis": ("Not a retail closing day" if status == "open" else
                                    "Company policy: close at 5 p.m." if (status == "reduced hours" and prov != "QC")
                                    else legal.loc[prov, "statute"]),
                    "source_id": legal.loc[prov, "source_id"],
                })
    return pd.DataFrame(rows).sort_values(["date", "province"]).reset_index(drop=True)
