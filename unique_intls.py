# Get the top-3 busiest train stations
import duckdb
import time
import numpy as np
import matplotlib.pyplot as plt
import polars as pl
import twomillionlines as tm
import datetime

x = duckdb.sql(f"""
        SELECT DISTINCT on(NORAD_CAT_ID) NORAD_CAT_ID, INTL_DES
        FROM 'database/tles.parquet'
        WHERE length(INTL_DES) > 0
        ORDER BY NORAD_CAT_ID ASC
        """).pl()
    
for row in x.iter_rows():
    print(row)
