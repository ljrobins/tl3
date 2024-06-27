import duckdb
import polars as pl
import numpy as np
import datetime

target_quantity_per_request = 1.5e5

x = duckdb.query("""
    SELECT * FROM 
    (SELECT DISTINCT date_trunc('day', EPOCH) as DAY, count(*) as count
    FROM 'database/tles_by_date.parquet'
    GROUP BY date_trunc('day', EPOCH)
    )
    ORDER BY DAY ASC
""").pl()

x = x.with_columns(
    pl.col('count').cum_sum().alias('cumsum')
).cast({'cumsum': int})
x = x.with_columns(
    accum_since = pl.col('cumsum') % target_quantity_per_request
).cast({'accum_since': int})
x = x.with_columns(
    req_indices = pl.when(pl.col('accum_since')>=pl.col('accum_since').shift(1))
            .then(pl.lit(0, dtype=pl.Boolean))
            .otherwise(pl.lit(1, dtype=pl.Boolean))
)

dates_query = x.filter(pl.col('req_indices'))
dates_query = dates_query.with_columns(
    accum_since = pl.col('cumsum')-pl.col('cumsum').shift(1)
)

print(dates_query)
print(dates_query['accum_since'].sum())

print(np.array(dates_query['DAY'].to_list()))

date_list = [datetime.datetime(x.year, x.month, x.day) for x in dates_query['DAY'].to_list()]
np.save('query_dates.npy', np.array(date_list), allow_pickle=True)