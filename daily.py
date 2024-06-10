import twomillionlines as tm
import duckdb
import polars as pl
import datetime
import os

if __name__ == "__main__":
    now = datetime.datetime.now()
    today = datetime.datetime(now.year, now.month, now.day)
    diri = 'data_st'
    files = [x for x in os.listdir(diri) if os.path.getsize(os.path.join(diri, x))]
    files = sorted(files, key=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d.txt'))

    days_back = 0
    dates = []
    while True:
        date = today - datetime.timedelta(days=days_back)
        if date.strftime("%Y-%m-%d.txt") not in files:
            dates.append(date)
        else:
            break
        days_back += 1

    tm.save_tles(list(reversed(dates)))
    tm.build_df("tles")