import datetime
import time

import duckdb
import polars as pl

import tl3

duckdb.sql(f"""
    COPY
        (SELECT * FROM '{tl3.DB_PATH}'
         ORDER BY EPOCH, NORAD_CAT_ID)
        TO 'tl3/processed/twoline2.parquet'
        (FORMAT 'parquet', COMPRESSION 'lz4');
""")

# endd

duckdb.sql(f"""
    COPY
        (SELECT * FROM '{tl3.DB_PATH}'
         ORDER BY NORAD_CAT_ID, EPOCH)
        TO 'tl3/processed/twolinen.parquet'
        (FORMAT 'parquet', COMPRESSION 'lz4');
""")


norad_id = 25544
date_start = datetime.datetime(2024, 8, 1)

t1 = time.time()
df_pl = (
    pl.scan_parquet('tl3/processed/twolinen.parquet')
    .filter(pl.col('NORAD_CAT_ID') == norad_id)
    .collect()
)
tpl = time.time() - t1
print(f'Polars ({pl.__version__}) filter NORAD: {tpl:.2f} sec')


t1 = time.time()
df_pl = (
    pl.scan_parquet('tl3/processed/twoline.parquet')
    .filter(pl.col('EPOCH') > date_start)
    .collect()
)
tpl = time.time() - t1
print(f'Polars ({pl.__version__}) filter EPOCH: {tpl:.2f} sec')

print(df_pl)
