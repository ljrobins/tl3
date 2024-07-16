import duckdb
import polars as pl
import time
import datetime

db_path = 'tl3/processed/twoline.parquet'

x = duckdb.sql(
    f"""
    SELECT DISTINCT row_group_bytes
    FROM parquet_metadata('{db_path}');
    """
)
print(x)

pl_res = (
    pl.scan_parquet(db_path)
    .filter(pl.col('EPOCH') > datetime.datetime(2024, 4, 1))
    .filter(pl.col('NORAD_CAT_ID') == 25544)
    .explain()
)
print(pl_res)


def test1():
    t1 = time.time()
    duck_res = duckdb.sql(
        f"""
        SELECT * FROM '{db_path}'
        WHERE NORAD_CAT_ID = 25544
        """
    ).pl()
    print(time.time() - t1)

    t1 = time.time()
    pl_res = pl.scan_parquet(db_path).filter(pl.col('NORAD_CAT_ID') == 25544).collect()
    print(time.time() - t1)


def test2():
    t1 = time.time()
    duck_res = duckdb.sql(
        f"""
        SELECT * FROM '{db_path}'
        WHERE EPOCH > '2024-04-01'
        """
    ).pl()
    print(time.time() - t1)

    t1 = time.time()
    pl_res = (
        pl.scan_parquet(db_path)
        .filter(pl.col('EPOCH') > datetime.datetime(2024, 4, 1))
        .collect()
    )
    print(time.time() - t1)


def test3():
    t1 = time.time()
    duck_res = duckdb.sql(
        f"""
        SELECT * FROM '{db_path}'
        WHERE EPOCH > '2024-04-01'
        AND NORAD_CAT_ID = 25544
        """
    ).pl()
    print(time.time() - t1)

    t1 = time.time()
    pl_res = (
        pl.scan_parquet(db_path)
        .filter(pl.col('EPOCH') > datetime.datetime(2024, 4, 1))
        .filter(pl.col('NORAD_CAT_ID') == 25544)
        .collect()
    )
    print(time.time() - t1)


def test4():
    t1 = time.time()
    duck_res = duckdb.sql(
        f"""
        SELECT * FROM '{db_path}'
        WHERE NORAD_CAT_ID = 25544
        AND EPOCH > '2024-04-01'
        """
    ).pl()
    print(time.time() - t1)

    t1 = time.time()
    df = (
        pl.scan_parquet(db_path)
        .filter(pl.col('NORAD_CAT_ID') == 25544)
        .filter(pl.col('EPOCH') > datetime.datetime(2024, 4, 1))
        .collect()
    )
    print(time.time() - t1)


test1()
test2()
test3()
test4()
