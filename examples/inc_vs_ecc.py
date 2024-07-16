"""
Inclination vs Eccentricity
===========================
"""

import colorcet as cc
import matplotlib.colors as colors
import matplotlib.pyplot as plt
from fast_histogram import histogram2d
import numpy as np
import tl3
import duckdb
import os


x = (
    duckdb.sql(f"""
    SELECT INC FROM {repr(tl3.DB_PATH)}
""")
    .pl()['INC']
    .to_numpy()
)

y = (
    duckdb.sql(f"""
    SELECT ECC FROM {repr(tl3.DB_PATH)}
""")
    .pl()['ECC']
    .to_numpy()
)

cmap = cc.cm['fire'].copy()
cmap.set_bad(cmap.get_under())  # set the color for 0
bounds = [[x.min(), x.max()], [y.min(), y.max()]]
extent = [x.min(), x.max(), y.min(), y.max()]

h = np.flipud(histogram2d(x, y, range=bounds, bins=365).T)
plt.imshow(h, norm=colors.LogNorm(vmin=1, vmax=h.max()), cmap=cmap, extent=extent)
plt.gca().set_aspect('auto')
plt.xlabel('Inclination [deg]')
plt.ylabel('Eccentricity')
plt.colorbar()
plt.tight_layout()
plt.show()
