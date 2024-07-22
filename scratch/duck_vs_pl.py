import duckdb
import polars as pl
import time
import datetime

db_path = 'tl3/processed/twoline.parquet'

def test1():
    t1 = time.time()
    duck_res = duckdb.sql(
        f"""
        SELECT * FROM '{db_path}'
        WHERE NORAD_CAT_ID = 25544
        """
    ).pl()
    print(f'DuckDB norad constraint {time.time() - t1:.2f} sec')

    t1 = time.time()
    pl_res = pl.scan_parquet(db_path).filter(pl.col('NORAD_CAT_ID') == 25544).collect()
    print(f'Polars norad constraint {time.time() - t1:.2f} sec')


def test2():
    t1 = time.time()
    duck_res = duckdb.sql(
        f"""
        SELECT * FROM '{db_path}'
        WHERE EPOCH > '2024-04-01'
        """
    ).pl()
    print(f'DuckDB epoch constraint {time.time() - t1:.2f} sec')

    t1 = time.time()
    pl_res = (
        pl.scan_parquet(db_path)
        .filter(pl.col('EPOCH') > datetime.datetime(2024, 4, 1))
        .collect()
    )
    print(f'Polars epoch constraint {time.time() - t1:.2f} sec')


def test3():
    t1 = time.time()
    duck_res = duckdb.sql(
        f"""
        SELECT * FROM '{db_path}'
        WHERE EPOCH > '2024-04-01'
        AND NORAD_CAT_ID = 25544
        """
    ).pl()
    print(f'DuckDB two constraints, epoch first {time.time() - t1:.2f} sec')

    t1 = time.time()
    pl_res = (
        pl.scan_parquet(db_path)
        .filter(pl.col('EPOCH') > datetime.datetime(2024, 4, 1))
        .filter(pl.col('NORAD_CAT_ID') == 25544)
        .collect()
    )
    print(f'Polars two constraints, epoch first {time.time() - t1:.2f} sec')


def test4():
    t1 = time.time()
    duck_res = duckdb.sql(
        f"""
        SELECT * FROM '{db_path}'
        WHERE NORAD_CAT_ID = 25544
        AND EPOCH > '2024-04-01'
        """
    ).pl()
    print(f'DuckDB two constraints, epoch last {time.time() - t1:.2f} sec')

    t1 = time.time()
    df = (
        pl.scan_parquet(db_path)
        .filter(pl.col('NORAD_CAT_ID') == 25544)
        .filter(pl.col('EPOCH') > datetime.datetime(2024, 4, 1))
        .collect()
    )
    print(f'Polars two constraints, epoch last {time.time() - t1:.2f} sec')


test1()
print()
test2()
print()
test3()
print()
test4()
