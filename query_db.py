import sqlite3
import time
import polars as pl
import matplotlib.pyplot as plt

db_path = "tles2.db"
con = sqlite3.connect(db_path, cached_statements=500)
cur = con.cursor()
columns_info = cur.execute("PRAGMA table_info(TLE)").fetchall()
print(cur.execute("PRAGMA index_list(TLE)").fetchall())
column_names = [info[1] for info in columns_info]
# column_names = ["EPOCH"]

norad_id = 25544
epoch_start = '2024-01-01 00:00:00.000'
epoch_end = '2024-01-02 00:00:00.000'
sel_cols = column_names

t1 = time.time()
res = cur.execute(f"SELECT {', '.join(sel_cols)} FROM TLE WHERE NORAD_CAT_ID={norad_id} AND EPOCH > {repr(epoch_start)} AND EPOCH < {repr(epoch_end)} ORDER BY EPOCH")
x = res.fetchall()
print(time.time()-t1)

t1 = time.time()
res = cur.execute(f"SELECT {', '.join(sel_cols)} FROM TLE WHERE NORAD_CAT_ID={norad_id} AND EPOCH > {repr(epoch_start)} AND EPOCH < {repr(epoch_end)} ORDER BY EPOCH")
x = res.fetchall()
print(time.time()-t1)

df = pl.DataFrame(x)
df = df.rename({k:v for k,v in zip(df.columns, sel_cols)})
df = df.with_columns([
    pl.col('EPOCH').str.to_datetime("%Y-%m-%d %H:%M:%S%.f")
])


enddd

plt.hist(df['EPOCH'], bins=365)
plt.show()

plt.plot(df['EPOCH'], df['ECC'])
plt.show()