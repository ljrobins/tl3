import duckdb
import time
import numpy as np
import matplotlib.pyplot as plt
import polars as pl
import twomillionlines as tm
import datetime
from typing import List, Union

# dummy for warm start
x = tm.tles_between(datetime.datetime(2024,1,1), datetime.datetime(2024,1,2), norad_cat_id='all', return_as='polars')

t1 = time.time()
x = tm.tles_between(datetime.datetime(2023,1,1), datetime.datetime(2023,1,2), norad_cat_id='all', return_as='polars')
print(time.time()-t1)

t1 = time.time()
x = tm.tles_between(datetime.datetime(2022,1,1), datetime.datetime(2024,1,1), norad_cat_id='25544', return_as='polars')
print(time.time()-t1)

print(x)

print(duckdb.sql("SELECT count(*) FROM 'database/noice_by_date.parquet'"))
