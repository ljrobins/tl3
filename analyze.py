import colorcet as cc
import matplotlib.colors as colors
import matplotlib.pyplot as plt
from fast_histogram import histogram2d
import polars as pl
import matplotlib.pyplot as plt
import numpy as np

df = pl.read_parquet('database/db.parquet')

X = np.floor(df['EPOCH_DAY_OF_YEAR'].to_numpy())
Y = df['EPOCH_DAY_OF_YEAR'].to_numpy()
Y -= np.floor(Y)
Y *= 24

# epoch = (df['EPOCH_YEAR'] + df['EPOCH_DAY_OF_YEAR'] / 365.25).to_numpy()
# inds = df['NORAD_CAT_ID'].to_numpy() == 5
# X = epoch[inds]
# Y = df['N'].to_numpy()[inds]

# plt.hist2d(X,Y, bins=100)
# plt.show()
# endd


cmap = cc.cm["fire"].copy()
cmap.set_bad(cmap.get_under())  # set the color for 0
bounds = [[X.min(), X.max()], [Y.min(), Y.max()]]
extent = [X.min(), X.max(), Y.min(), Y.max()]
print(bounds)
h = np.flipud(histogram2d(X, Y, range=bounds, bins=365).T)
plt.imshow(h, norm=colors.LogNorm(vmin=1, vmax=h.max()), cmap=cmap, extent=extent)
plt.gca().set_aspect('auto')
plt.show()