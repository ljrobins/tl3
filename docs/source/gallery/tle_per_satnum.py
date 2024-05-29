"""
TLE Production Per Satnum
=========================

Plotting TLE production as a function of satnum
"""

import twomillionlines as tm

import matplotlib.pyplot as plt
import numpy as np
import colorcet as cc
import matplotlib.pyplot as plt

df = tm.get_df()
print(df)

nodes, inv, counts = np.unique(df['NORAD_CAT_ID'].to_numpy(), return_inverse=True, return_counts=True)
del df

max_counts = counts[np.argsort(-counts)]
max_nodes = nodes[np.argsort(-counts)]

n_snoopi_tles = max_counts[max_nodes==59563]
print(max_counts)
print(max_nodes)
print(n_snoopi_tles)

plt.scatter(np.arange(max_counts.size), max_counts, s=1)
plt.show()

plt.hist2d(nodes, counts, bins=250, cmap=cc.cm["fire"].copy())
plt.tight_layout()
plt.grid()
plt.show()