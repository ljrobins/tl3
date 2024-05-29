import polars as pl
import sqlite3
import os
from tqdm import tqdm

name = 'tles'
db_path = f"{name}.db"
df = pl.read_parquet(f"database/{name}.parquet")

if os.path.exists(db_path):
    os.remove(db_path)

con = sqlite3.connect(db_path)
cur = con.cursor()
columns = ', '.join(df.columns)
column_defs = ", ".join([f"{col} DATETIME" if col == "EPOCH" else f"{col} TEXT" if df[col].dtype == pl.Utf8 else f"{col} REAL" if (df[col].dtype == pl.Float64 or df[col].dtype == pl.Float32) else f"{col} INTEGER" for col in df.columns])

cur.execute(f"""
    CREATE TABLE TLE (
        {column_defs}
    )
""")

template = ("?, " * df.width)[:-2]

for row in tqdm(df.iter_rows()):
    cur.execute(f"INSERT INTO TLE ({columns}) VALUES ({template})", row)

idx_cols = ["NORAD_CAT_ID", "EPOCH"]
for idx_col in idx_cols:
    print(f"Creating index on {idx_col}")
    cur.execute(f"CREATE INDEX idx_{idx_col.lower()} ON TLE({idx_col})")

con.commit()
