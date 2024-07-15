"""
TLE Production Per Hour of the Day
==================================

Daily TLE production in UTC
"""

import twomillionlines as tm

import matplotlib.pyplot as plt
import polars as pl

df = tm.get_df()
hour_of_day = df.select(
    pl.col('EPOCH').dt.hour()
    + pl.col('EPOCH').dt.minute() / 60
    + pl.col('EPOCH').dt.second() / 3600
)

plt.hist(hour_of_day, bins=500)
plt.xlabel('Hour of the day')
plt.ylabel('TLEs Produced')
plt.tight_layout()
plt.grid()
plt.show()
