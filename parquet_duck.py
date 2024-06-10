# Get the top-3 busiest train stations
import duckdb
import time
import numpy as np
import matplotlib.pyplot as plt
import polars as pl
import twomillionlines as tm
import datetime
from typing import List, Union

def tles_between(date_start: datetime.datetime, 
                     date_end: datetime.datetime, 
                     norad_cat_id: Union[int, str] = 'all',
                     cols: List[str] = '*',
                     return_as: str = 'polars'):
    assert return_as.lower() in ['polars', 'tle'], "return_as must be 'polars' or 'tle'"
    assert date_end > date_start, "date_start must be before date_end"
    norad_cat_id = str(norad_cat_id)
    if norad_cat_id.lower() != 'all':
        assert int(norad_cat_id) < 1e5, "norad_cat_id must be < 100_000"
    
    idstr, fdstr = date_start.strftime("%Y-%m-%d"), date_end.strftime("%Y-%m-%d")
    constraints = []
    constraints.append(f'EPOCH BETWEEN {repr(idstr)} AND {repr(fdstr)}')
    if norad_cat_id.lower() != 'all' and norad_cat_id.isdigit():
        constraints.append(f'NORAD_CAT_ID=={norad_cat_id}')
    
    db = 'database/tles_by_date.parquet'
    
    if isinstance(cols, list):
        col_repr = ', '.join(cols)
    elif isinstance(cols, str):
        col_repr = cols
    else:
        raise NotImplementedError("cols must be of type list or str")

    query_str = f"""
        SELECT {col_repr}
        FROM {repr(db)}
        {'WHERE ' + ' AND '.join(constraints)}
        ORDER BY EPOCH ASC;
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

# dummy for warm start
x = tles_between(datetime.datetime(2024,1,1), datetime.datetime(2024,1,2), norad_cat_id='all', return_as='polars')

t1 = time.time()
x = tles_between(datetime.datetime(2023,1,1), datetime.datetime(2023,1,2), norad_cat_id='all', return_as='polars')
print(time.time()-t1)    

t1 = time.time()
x = tles_between(datetime.datetime(2023,1,1), datetime.datetime(2023,2,1), norad_cat_id=25544, return_as='polars')
print(time.time()-t1)

plt.plot(x['EPOCH'], x['ECC'])
plt.show()