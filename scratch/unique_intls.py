# Get the top-3 busiest train stations
import duckdb

x = duckdb.sql("""
        SELECT DISTINCT on(NORAD_CAT_ID) NORAD_CAT_ID, INTL_DES
        FROM 'database/tles.parquet'
        WHERE length(INTL_DES) > 0
        ORDER BY NORAD_CAT_ID ASC
        """).pl()

for row in x.iter_rows():
    print(row)
