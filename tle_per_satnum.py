import polars as pl
import matplotlib.pyplot as plt
import numpy as np
import colorcet as cc
import matplotlib.colors as colors
import matplotlib.pyplot as plt
from fast_histogram import histogram2d

df = pl.read_parquet('database/db.parquet')

x = df['NORAD_CAT_ID'].to_numpy()

nodes, inv, counts = np.unique(x, return_inverse=True, return_counts=True)

plt.hist2d(nodes, counts, bins=250, cmap=cc.cm["fire"].copy())
plt.tight_layout()
plt.show()