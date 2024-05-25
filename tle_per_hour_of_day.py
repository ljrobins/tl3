import polars as pl
import matplotlib.pyplot as plt
import numpy as np

df = pl.read_parquet('database/db.parquet')

doy = df['EPOCH_DAY_OF_YEAR'].to_numpy()
hour_of_day = 24 * (doy - np.floor(doy))

plt.hist(hour_of_day, bins=500)
plt.xlabel("Hour of the day")
plt.ylabel("TLEs Produced")
plt.tight_layout()
plt.show()