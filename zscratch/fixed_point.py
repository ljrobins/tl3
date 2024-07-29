import tl3
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import detrend

tles = tl3.tles_between(date_start=None, date_end=None, identifier=25544)
tles = tles.drop(['INTL_DES', 'N_DOT', 'N_DDOT', 'CHECKSUM1', 'CHECKSUM2', 'COSPAR_ID', 'B_STAR', 'ELSET_NUM', 'REV_NUM', 'NORAD_CAT_ID'])

print(tles)

raan = np.unwrap(tles['RAAN'].to_numpy(), period=360)
n = tles['N'].to_numpy()
plt.plot(tles['EPOCH'], n)
plt.show()