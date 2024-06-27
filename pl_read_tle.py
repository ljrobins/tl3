import os
import polars as pl
import datetime
import time

diri = 'data2'
files = [x for x in os.listdir(diri) if os.path.getsize(os.path.join(diri, x))]
files = sorted(files, key=lambda x: datetime.datetime.strptime(x[:10], '%Y-%m-%d'))
dfs = {}
i = 0

def l1_l2_df_from_tle_file(fpath: str) -> pl.DataFrame:
    df = pl.read_csv(fpath, has_header=False)
    df = df.with_row_index()
    df = df.with_columns(
        pl.when(pl.col('column_1').str.head(1) == '1')
        .then(1)
        .otherwise(2)
        .alias('line_num'),
        pl.col('index') // 2
    )
    bad_inds = (df['line_num'].shift(fill_value=2) + df['line_num'].shift(n=-1, fill_value=1) - df['line_num']) != 1
    df = df.filter(bad_inds)
    df = df.pivot(
        index="index", columns="line_num", values='column_1'
    )
    df = df.rename(
        {'1': 'TLE_LINE1', '2': 'TLE_LINE2',}
    )
    return df

t1 = time.time()
df = l1_l2_df_from_tle_file('data2/2017-11-05 2017-11-11.txt')
t2 = time.time()
print(t2-t1)

print(df)