"""
TLE Production Per Day
======================

Plotting the number of TLEs produced every day since 1958
"""

import tl3

import matplotlib.pyplot as plt
import duckdb

x = duckdb.sql(f"""
    SELECT EPOCH FROM {repr(tl3.DB_PATH)}
""").pl()['EPOCH']

range_days = int((x.max() - x.min()).total_seconds() / 86400 / 2)
plt.hist(x, bins=range_days)
plt.xlabel('Year')
plt.ylabel('TLEs Per Day')
plt.grid()
plt.tight_layout()
plt.show()
