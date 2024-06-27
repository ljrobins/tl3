import duckdb

x = duckdb.sql("""
    select count(*) from 'database/noice_by_date.parquet'
    where NORAD_CAT_ID=25544
""")

print(x)