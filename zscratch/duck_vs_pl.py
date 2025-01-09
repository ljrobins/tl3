import datetime
import time

import duckdb
import polars as pl

# os.environ['POLARS_VERBOSE'] = '1'

db_path = 'tl3/processed/twoline.parquet'

vduck = duckdb.__version__
vpl = pl.__version__

norad_id = 25544
date_start = datetime.datetime(2023, 4, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
date_end = date_start + datetime.timedelta(days=2)
cols = '*'
par_strat = 'auto'
engine = 'cpu'


def test1():
    t1 = time.time()
    df_duck = duckdb.sql(
        f"""
        SELECT {cols} FROM '{db_path}'
        WHERE NORAD_CAT_ID = {norad_id}
        """
    ).pl()
    tduck = time.time() - t1
    print(f'DuckDB ({vduck}) filter NORAD, select {cols}: {tduck:.2f} sec')

    t1 = time.time()
    df_pl = (
        pl.scan_parquet(db_path, parallel=par_strat)
        .filter(pl.col('NORAD_CAT_ID') == norad_id)
        .select(*cols.replace(' ', '').split(','))
        .collect(engine=engine)
    )
    tpl = time.time() - t1
    print(f'Polars ({vpl}) filter NORAD, select {cols}: {tpl:.2f} sec')
    print(f'Polars is {tduck/tpl:.1f}x faster')

    df_duck = df_duck.with_columns(pl.col('EPOCH').dt.convert_time_zone('UTC'))
    assert df_duck.equals(df_pl)
    print()
    return tduck, tpl


def test2():
    t1 = time.time()
    df_duck = duckdb.sql(
        f"""
        SELECT {cols} FROM '{db_path}'
        WHERE EPOCH > '{date_start.isoformat()}'
        AND EPOCH < '{date_end.isoformat()}'
        """
    ).pl()
    tduck = time.time() - t1
    print(f'DuckDB ({vduck}) filter epoch, select {cols}: {tduck:.2f} sec')

    t1 = time.time()
    df_pl = (
        pl.scan_parquet(db_path, parallel=par_strat)
        .filter(pl.col('EPOCH') > date_start, pl.col('EPOCH') < date_end)
        .select(*cols.replace(' ', '').split(','))
        .collect(engine=engine)
    )
    tpl = time.time() - t1

    print(f'Polars ({vpl}) filter epoch, select {cols}: {tpl:.2f} sec')
    print(f'Polars is {tduck/tpl:.1f}x faster')

    df_duck = df_duck.with_columns(pl.col('EPOCH').dt.convert_time_zone('UTC'))

    assert df_duck.equals(df_pl)
    print()
    return tduck, tpl


def test3():
    t1 = time.time()
    df_duck = duckdb.sql(
        f"""
        SELECT {cols} FROM '{db_path}'
        WHERE EPOCH > '{date_start.isoformat()}'
        AND EPOCH < '{date_end.isoformat()}'
        AND NORAD_CAT_ID = {norad_id}
        """
    ).pl()
    tduck = time.time() - t1
    print(f'DuckDB ({vduck}) filter NORAD & epoch, select {cols}: {tduck:.2f} sec')

    t1 = time.time()
    df_pl = (
        pl.scan_parquet(db_path, parallel=par_strat)
        .filter(pl.col('EPOCH') > date_start)
        .filter(pl.col('EPOCH') < date_end)
        .filter(pl.col('NORAD_CAT_ID') == norad_id)
        .select(*cols.replace(' ', '').split(','))
        .collect(engine=engine)
    )
    tpl = time.time() - t1
    print(f'Polars ({vpl}) filter NORAD & epoch, select {cols}: {tpl:.2f} sec')
    print(f'Polars is {tduck/tpl:.1f}x faster')

    df_duck = df_duck.with_columns(pl.col('EPOCH').dt.convert_time_zone('UTC'))

    assert df_duck.equals(df_pl)
    print()
    return tduck, tpl


test1()
test2()
test3()
