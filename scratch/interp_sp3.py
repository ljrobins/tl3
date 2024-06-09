import polars as pl
from scipy.interpolate import Akima1DInterpolator, PchipInterpolator, interp1d, BarycentricInterpolator
import datetime
import os
import time
import numpy as np
import matplotlib.pyplot as plt
import mirage as mr

d1 = datetime.datetime(2024, 3, 3)
d2 = datetime.datetime(2024, 3, 3, 12)
total_seconds = (d2-d1).total_seconds()
gps_epoch = datetime.datetime(1980, 1, 6)

interp_buffer = datetime.timedelta(hours=1.5)

d1_with_buffer = d1 - interp_buffer
d2_with_buffer = d2 + interp_buffer

d1_with_buffer_days_since_epoch = (d1_with_buffer-gps_epoch).total_seconds()/86400
d2_with_buffer_days_since_epoch = (d2_with_buffer-gps_epoch).total_seconds()/86400
gps_wk_start = int(d1_with_buffer_days_since_epoch//7)
gps_wk_end = int(d2_with_buffer_days_since_epoch//7)

t1 = time.time()
dfs = []
for wk in range(gps_wk_start, gps_wk_end+1):
     dfs.append(pl.read_parquet(os.path.join('proc', 'gnss', f'{wk}.parquet')))
if len(dfs) > 1:
    df = pl.concat(dfs, how='diagonal').unique('date')
else:
    df = dfs[0]
df = df.filter((pl.col('date') >= d1_with_buffer) & (pl.col('date') <= d2_with_buffer)).sort('date')
arr = df.select(pl.exclude('date').fill_null(np.inf)).to_numpy()
epsec = df.select(pl.col('date').diff().dt.total_seconds().cum_sum().fill_null(0).cast(pl.Float64)).to_numpy().flatten()
first_interp_date = df.select(pl.col('date').min()).to_numpy().flatten()[0].tolist()
epsec -= (d1 - first_interp_date).total_seconds()
print(time.time()-t1)

coe1 = mr.rv_to_coe(arr[:,:3])
print(coe1)
endd
ff = 10

fit_inds = np.arange(0, epsec.size, ff)
test_inds = np.argwhere((epsec > 0) & (epsec < total_seconds)).flatten()
test_inds = np.setdiff1d(test_inds, fit_inds)

epsec_fit = epsec[fit_inds]
arr_fit = arr[fit_inds,:]
epsec_test = epsec[test_inds]
arr_test = arr[test_inds,:]

interpers = []
t1 = time.time()
interpers.append(('linear', interp1d(epsec_fit, arr_fit, copy=False,
                 axis=0, kind='linear')))
interpers.append(('cubic spline', interp1d(epsec_fit, arr_fit, copy=False,
                 axis=0, kind='cubic')))
interpers.append(('quadratic spline', interp1d(epsec_fit, arr_fit, copy=False,
                 axis=0, kind='quadratic')))
interpers.append(('akima', Akima1DInterpolator(epsec_fit, arr_fit)))
interpers.append(('modified akima', Akima1DInterpolator(epsec_fit, arr_fit, method='makima')))
interpers.append(('pchip', PchipInterpolator(epsec_fit, arr_fit)))
interpers.append(('barycentric', BarycentricInterpolator(epsec_fit, arr_fit)))
print(time.time()-t1)

for name, interper in interpers:
    t1 = time.time()
    yi = interper(epsec_test)
    print(f'{name:20}{time.time()-t1:.2e} interp time')
    abs_err = np.abs(yi-arr[test_inds,:])

    mean_error_per_sat = np.mean(abs_err, axis=0, where=abs_err != 0)
    std_error_per_sat = np.std(abs_err, axis=0, where=abs_err != 0)
    mean_error_over_time = np.mean(abs_err, axis=1)
    std_error_over_time = np.std(abs_err, axis=1)
    plt.subplot(2,2,1)
    plt.plot(mean_error_per_sat, label=name)
    plt.yscale('log')
    plt.subplot(2,2,2)
    plt.plot(std_error_per_sat, label=name)
    plt.yscale('log')
    plt.legend()
    plt.subplot(2,2,3)
    plt.plot(std_error_over_time, label=name)
    plt.yscale('log')
    plt.subplot(2,2,4)
    plt.plot(std_error_over_time, label=name)
    plt.yscale('log')


plt.show()

