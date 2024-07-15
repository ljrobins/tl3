"""
TLE Production Per Day
======================

Plotting the number of TLEs produced every day since 1958
"""

import twomillionlines as tm

import matplotlib.pyplot as plt
import time

t1 = time.time()
df = tm.get_df()
print(f'read time: {time.time()-t1:.2f} seconds')

x = df['EPOCH']
del df
range_days = int((x.max() - x.min()).total_seconds() / 86400)
plt.hist(x, bins=range_days)
plt.xlabel('Year')
plt.ylabel('TLEs Per Day')
plt.grid()
plt.show()
