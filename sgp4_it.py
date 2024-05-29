
import sqlite3
import time
import polars as pl
import matplotlib.pyplot as plt
import datetime
from sgp4.api import WGS72, Satrec
from tqdm import tqdm
import numpy as np
from astropy.time import Time
from scipy.ndimage import median_filter

def running_mean(x, N):
    print(x.shape)
    x = x.copy().flatten()
    x[np.isnan(x)] = x[np.argwhere(np.isnan(x)).flatten()+1]
    cumsum = np.cumsum(np.insert(x, 0, 0)) 
    return (cumsum[N:] - cumsum[:-N]) / float(N)


db_path = "tles2.db"
cur = sqlite3.connect(db_path).cursor()

cur.execute("PRAGMA table_info(TLE)")
columns_info = cur.fetchall()

column_names = [info[1] for info in columns_info]

# norad_id = 15039
norad_id = 25544
epoch_start = '1900-01-01 00:00:00.000'
epoch_end = '2025-01-01 00:00:00.000'
sel_cols = column_names

t1 = time.time()
res = cur.execute(f"SELECT {', '.join(sel_cols)} FROM TLE WHERE NORAD_CAT_ID={norad_id} AND EPOCH > {repr(epoch_start)} AND EPOCH < {repr(epoch_end)} ORDER BY EPOCH")
x = res.fetchall()
df = pl.DataFrame(x)
df = df.rename({k:v for k,v in zip(df.columns, sel_cols)})
df = df.with_columns([
    pl.col('EPOCH').str.to_datetime("%Y-%m-%d %H:%M:%S%.f")
])
print(time.time()-t1)


def init_sat_from_row(row):
    days_since = (row['EPOCH'][0] - datetime.datetime(1949, 12, 31, 1, 1, 00, 00)).total_seconds() / 86400
    sat = Satrec()

    sat.sgp4init(
        WGS72,                # gravity model
        'i',                  # 'a' = old AFSPC mode, 'i' = improved mode
        row['NORAD_CAT_ID'][0],                # satnum: Satellite number
        days_since,       # epoch: days since 1949 December 31 00:00 UT
        row['B_STAR'][0],           # bstar: drag coefficient (1/earth radii)
        0.0,                  # ndot: ballistic coefficient (radians/minute^2) (not used, set to zero)
        0.0,                  # nddot: mean motion 2nd derivative (radians/minute^3) (not used, set to zero)
        row['ECC'][0],            # ecco: eccentricity
        np.deg2rad(row['AOP'][0]),   # argpo: argument of perigee (radians)
        np.deg2rad(row['INC'][0]),   # inclo: inclination (radians)
        np.deg2rad(row['MA'][0]),   # mo: mean anomaly (radians)
        row['N'][0] / 1440 * (2 * np.pi),  # no_kozai: mean motion (radians/minute)
        np.deg2rad(row['RAAN'][0]),    # nodeo: R.A. of ascending node (radians)
    )
    return sat

mid_dates = []
jds_mid = []
prop_age = []
r_diff = []
v_diff = []

for i in tqdm(range(0, df.height-1)):
    r1 = df[i,:]
    r2 = df[i+1,:]
    sat1 = init_sat_from_row(r1)
    sat2 = init_sat_from_row(r2)

    to_mid = (r2['EPOCH'][0] - r1['EPOCH'][0]) / 2
    mid_date = r1['EPOCH'][0] + to_mid
    
    jd = Time(mid_date, format="datetime", scale="utc").jd

    e1, r1, v1 = sat1.sgp4(*np.modf(jd))
    e2, r2, v2 = sat2.sgp4(*np.modf(jd))

    mid_dates.append(mid_date)
    jds_mid.append(jd)
    prop_age.append(to_mid.total_seconds() / 3600)
    r_diff.append(np.linalg.norm(np.array(r1)-np.array(r2)))
    v_diff.append(np.linalg.norm(np.array(v1)-np.array(v2)))

jds_mid = np.array(jds_mid)
prop_age = np.array(prop_age)
r_diff = np.array(r_diff)
v_diff = np.array(v_diff)

r1 = median_filter(r_diff / prop_age, 1501, mode='nearest')
r2 = median_filter(v_diff / prop_age, 1501, mode='nearest')

plt.figure()
plt.scatter(prop_age, r_diff, s=1, alpha=0.2)
plt.yscale('log')

plt.figure()
plt.scatter(mid_dates, prop_age, s=1, alpha=0.2)
plt.yscale('log')


plt.figure()
plt.scatter(mid_dates, r_diff / prop_age, s=1, alpha=0.2, color='b')
plt.scatter(mid_dates, v_diff / prop_age, s=1, alpha=0.2, color='orange')
plt.plot(mid_dates, r1, color='c')
plt.plot(mid_dates, r2, color='m')
plt.yscale('log')
plt.show()