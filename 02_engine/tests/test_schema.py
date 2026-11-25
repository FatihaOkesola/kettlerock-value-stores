"""The PostgreSQL table definitions must match the canonical CSVs column for column."""
import re

from kettlerock_engine.config import ENGINE_ROOT

RESERVED = {"case", "order", "group", "user", "table", "select", "from", "where", "end", "default", "check"}


def _ddl_columns():
    sql = "\n".join(p.read_text(encoding="utf-8") for p in sorted((ENGINE_ROOT / "schemas").glob("0*.sql")))
    tables = {}
    for name, body in re.findall(r"CREATE TABLE (\w+) \((.*?)\n\);", sql, re.S):
        cols = [ln.strip().split()[0] for ln in body.strip().splitlines()
                if ln.strip() and not ln.strip().upper().startswith(("PRIMARY", "FOREIGN", "UNIQUE", "CONSTRAINT"))]
        tables[name] = cols
    return tables


def test_every_table_has_a_definition(tables, traffic_table):
    assert set(_ddl_columns()) == set(tables) | {"fact_traffic_day"}


def test_columns_match_csv_order(tables, traffic_table):
    ddl = _ddl_columns()
    for name, df in {**tables, "fact_traffic_day": traffic_table}.items():
        assert ddl[name] == list(df.columns), name


def test_no_reserved_words_as_column_names():
    for name, cols in _ddl_columns().items():
        assert not RESERVED & set(cols), name
