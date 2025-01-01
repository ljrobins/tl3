import tl3
import os
import polars as pl
import time

df = pl.read_parquet(os.environ['TL3_DB_PATH'])

print(df)

t1 = time.time()
for _ in range(200):
    df2 = df.filter(pl.col('NORAD_CAT_ID') == 25544)
print(time.time()-t1)