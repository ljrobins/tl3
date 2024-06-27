import twomillionlines as tm
import duckdb
import polars as pl
import datetime
import os
import numpy as np
import mirage as mr

if __name__ == "__main__":
    dates = np.load('query_dates.npy', allow_pickle=True)
    dates = list(reversed([x for x in dates]))
    
    diri = 'data2'
    tm.save_tles(dates, save_dir=diri, endpoint='tle')
