import duckdb
import polars as pl

import tl3

cospars = []
with open('../../fits-serv/interesting-norad-cool.txt', 'r') as f:
    for norad in f:
        cospars.append(tl3.norad_to_cospar(int(norad)))
cospars = sorted(list(set(cospars)), key=lambda x: int(x[:4]) + int(x[5:8]) / 1000)

df = duckdb.sql("""
    SELECT * FROM 'tl3/processed/satcat.parquet'
""").pl()

df = (
    df.filter(pl.col('INTLDES').str.contains_any(cospars))
    .select('INTLDES', 'NORAD_CAT_ID', 'OBJECT_TYPE', 'OBJECT_NAME')
    .sort('OBJECT_TYPE')
)
assert len(cospars) == df.height

pl.Config.set_tbl_rows(100)
print(df)

print('\n'.join(cospars))
