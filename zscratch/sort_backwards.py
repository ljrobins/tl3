import polars as pl

pl.read_parquet('tl3/processed/twoline.parquet').sort('NORAD_CAT_ID', 'EPOCH').write_parquet('tl3/processed/linetwo.parquet')