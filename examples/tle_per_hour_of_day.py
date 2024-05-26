"""
TLE Production Per Hour of the Day
==================================

Daily TLE production in UTC
"""

import twomillionlines as tm

import matplotlib.pyplot as plt
import numpy as np

df = tm.get_df()
print(df)

doy = df['EPOCH'].to_numpy()
hour_of_day = 24 * (doy - np.floor(doy))

plt.hist(hour_of_day, bins=500)
plt.xlabel("Hour of the day")
plt.ylabel("TLEs Produced")
plt.tight_layout()
plt.show()