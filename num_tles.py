import duckdb


n = duckdb.sql("SELECT COUNT(*) FROM 'database/tles_by_date.parquet'")

print(n)