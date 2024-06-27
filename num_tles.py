import duckdb


n = duckdb.sql("SELECT COUNT(*) FROM 'database/noice_by_date.parquet'")

print(n)