import polars as pl
import matplotlib.pyplot as plt

df = pl.read_parquet('database/db.parquet')
print(df)

x = df['EPOCH_DAY_OF_YEAR']/365 + df['EPOCH_YEAR']
range_days = int((x.max() - x.min()) * 365)
plt.hist(x, bins=range_days)
plt.xlabel("Year")
plt.ylabel("TLEs Per Day")
plt.show()