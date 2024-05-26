import sqlite3
import time
import polars as pl
import matplotlib.pyplot as plt

db_path = "tles.db"
cur = sqlite3.connect(db_path).cursor()

cur.execute("PRAGMA table_info(TLE)")
columns_info = cur.fetchall()

column_names = [info[1] for info in columns_info[1:]]

norad_id = 25544
epoch_start = '2023-01-01 00:00:00.000'
epoch_end = '2024-01-01 00:00:00.000'
sel_cols = column_names


t1 = time.time()
res = cur.execute(f"SELECT {', '.join(sel_cols)} FROM TLE WHERE NORAD_CAT_ID={norad_id} AND EPOCH > {repr(epoch_start)} AND EPOCH < {repr(epoch_end)} ORDER BY EPOCH")
x = res.fetchall()
print(time.time()-t1)

df = pl.DataFrame(x)
df = df.rename({k:v for k,v in zip(df.columns, sel_cols)})
df = df.with_columns([
    pl.col('EPOCH').str.to_datetime("%Y-%m-%d %H:%M:%S%.f")
])
print(df)

plt.hist(df['EPOCH'], bins=365)
plt.show()

plt.plot(df['EPOCH'], df['ECC'])
plt.show()