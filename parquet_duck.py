# Get the top-3 busiest train stations
import duckdb
import time
import numpy as np
import matplotlib.pyplot as plt
import polars as pl
import twomillionlines as tm
import datetime
from typing import List, Union

def get_tles_between(date_start: datetime.datetime, 
                     date_end: datetime.datetime, 
                     norad_cat_id: Union[int, str, None] = None,
                     cols: List[str] = '*',
                     return_as: str = 'polars'):
    assert return_as.lower() in ['polars', 'tle'], "return_as must be 'polars' or 'tle'"
    assert date_end > date_start, "date_start must be before date_end"
    if norad_cat_id is not None:
        assert norad_cat_id < 1e5, "norad_cat_id must be < 100_000"
    
    idstr, fdstr = date_start.strftime("%Y-%m-%d"), date_end.strftime("%Y-%m-%d")
    constraints = []
    constraints.append(f'EPOCH BETWEEN {repr(idstr)} AND {repr(fdstr)}')
    if norad_cat_id is not None and norad_cat_id.lower() != 'all':
        constraints.append(f'NORAD_CAT_ID=={norad_cat_id}')
        db = 'tles_by_id.parquet'
    else:
        db = 'tles_by_date.parquet'
    query_str = f"""
        SELECT {cols}
        FROM {repr(db)}
        {'WHERE ' + ' AND '.join(constraints)}
        ORDER BY EPOCH ASC
        """
    x = duckdb.sql(query_str).pl()
    
    if return_as.lower() == 'polars':
        return x
    elif return_as.lower() == 'tle':
        l1s = np.zeros(x.height, dtype='<U69')
        l2s = np.zeros(x.height, dtype='<U69')
        for i,row in enumerate(x.iter_rows(named=True)):
            l1s[i], l2s[i] = tm.df_row_to_tle(row)
        return l1s, l2s

# x = duckdb.sql("SELECT *FROM parquet_metadata('database/tles_row_grouped.parquet');").pl()
# print(x)
# endd

t1 = time.time()
x = get_tles_between(datetime.datetime(2023,1,1), 
                     datetime.datetime(2024,1,1), norad_cat_id=25544, return_as='polars')
print(time.time()-t1)

print(x.shape)

day_frac = x.select(pl.col('EPOCH').dt.hour().cast(pl.Float32) + 1 / 60 * pl.col('EPOCH').dt.minute().cast(pl.Float32))

plt.hist(day_frac, bins=(24 * 60))
plt.show()