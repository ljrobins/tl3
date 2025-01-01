import polars as pl

df = pl.read_parquet('tl3/processed/twoline.parquet')
df = df.filter(pl.col("EPOCH") < pl.date(2024, 5, 1))
df.write_parquet('half.parquet', compression='zstd')