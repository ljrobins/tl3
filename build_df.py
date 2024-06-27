import os
import numpy as np
import time
import datetime
from alive_progress import alive_bar
import polars as pl

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

def implied_decimal_to_float(s: pl.Series) -> pl.Expr:
    # s is a pl.col(col_name).str.slice(start, length) instance
    return (
        s.str.head(5).str.strip_chars().str.to_integer(strict=False) * (10.0**-4) * 10.0**s.str.tail(2).str.to_integer(strict=False)
    )

def process_df(df: pl.DataFrame) -> pl.DataFrame:
    df = df.filter(
        (pl.col('TLE_LINE1').str.len_chars() == 69),
        (pl.col('TLE_LINE2').str.len_chars() == 69),
        )
    df = df.with_columns(
        # pl.col('PUBLISH_EPOCH').str.to_datetime("%Y-%m-%d %H:%M:%S", time_unit='ms'),
        pl.col('TLE_LINE1').str.slice(2, 5).str.strip_chars().cast(pl.UInt32).alias('NORAD_CAT_ID'),
        pl.col('TLE_LINE1').str.slice(9, 8).str.strip_chars().str.replace_all(' ', '').alias('INTL_DES'),
        pl.col('TLE_LINE1').str.slice(18, 2).str.strip_chars().cast(pl.Int16).alias('EPOCH_YEAR'),
        pl.col('TLE_LINE1').str.slice(20, 12).str.strip_chars().cast(pl.Float32).alias('EPOCH_DAY'),
        pl.col('TLE_LINE1').str.slice(33, 10).str.strip_chars().cast(pl.Float32).alias('N_DOT'),
        implied_decimal_to_float(df['TLE_LINE1'].str.slice(44,8)).alias('N_DDOT'),
        implied_decimal_to_float(df['TLE_LINE1'].str.slice(53,8)).alias('B_STAR'),
        pl.col('TLE_LINE1').str.slice(64,4).str.strip_chars().cast(pl.UInt16).alias("ELSET_NUM"),
        pl.col('TLE_LINE1').str.slice(68,1).cast(pl.UInt8).alias("CHECKSUM1"),

        pl.col('TLE_LINE2').str.slice(8,7).str.strip_chars().cast(pl.Float32, strict=False).alias('INC'),
        pl.col('TLE_LINE2').str.slice(17,7).str.strip_chars().cast(pl.Float32, strict=False).alias('RAAN'),
        (pl.col('TLE_LINE2').str.slice(26,7).str.strip_chars().cast(pl.Float64, strict=False) * 10.0**-7).alias('ECC'),
        pl.col('TLE_LINE2').str.slice(34,7).str.strip_chars().cast(pl.Float32, strict=False).alias('AOP'),
        pl.col('TLE_LINE2').str.slice(43,7).str.strip_chars().cast(pl.Float32, strict=False).alias('MA'),
        pl.col('TLE_LINE2').str.slice(52,10).str.strip_chars().cast(pl.Float32, strict=False).alias('N'), # mean motion, revs/day
        pl.col('TLE_LINE2').str.slice(63,4).str.replace_all(' ', '0').cast(pl.UInt16, strict=False).alias('REV_NUM'),
        pl.col('TLE_LINE2').str.slice(68,1).cast(pl.UInt8).alias("CHECKSUM2"),
    )
    df = df.with_columns(
        pl.when(pl.col("EPOCH_YEAR") > 50).then(1900+pl.col("EPOCH_YEAR")).otherwise(2000+pl.col("EPOCH_YEAR")).alias("EPOCH_YEAR"),
    )
    df = df.with_columns(
        pl.from_epoch(
            pl.datetime(year=pl.col('EPOCH_YEAR'), month=1, day=1, time_unit='ms').dt.epoch('ms') + pl.col('EPOCH_DAY') * 86400 * 1e3,
            time_unit='ms'
        ).alias('EPOCH')
    )

    # df = df.with_columns(
    #     (pl.col('EPOCH') - pl.col('PUBLISH_EPOCH')).alias("PUBLICATION_AGE"),
    # )
    # df = df.with_columns(
    #     (pl.col('EPOCH') > drop_epochs_after_or_equal_to).alias('dropme')
    # )
    # print(df)
    # print(df['EPOCH'].min())
    # print(df['EPOCH'].max())
    height_before_drops = df.height
    df = df.drop('TLE_LINE1', 'TLE_LINE2', 'index').drop_nulls()

    if height_before_drops-df.height > 0:
        print(f'{f}: dropped {height_before_drops-df.height} rows containing nulls')
    # height_before_unique = df.height

    # df = df.unique()
    # if height_before_unique-df.height > 0:
    #     print(f'{f}: dropped {height_before_unique-df.height} duplicate rows')

    # df = df.filter(
    #     pl.col('PUBLICATION_AGE').dt.total_hours() < 7 * 24,
    #     pl.col('PUBLICATION_AGE').dt.total_hours() > -14 * 24
    # ) # make sure it isn't produced more than 1 day in the future, and  make sure it isn't produced more than 14 days in the past
    df = df.sort(['EPOCH', 'NORAD_CAT_ID'])
    return df



diri = 'data2'
files = [x for x in os.listdir(diri) if os.path.getsize(os.path.join(diri, x))]
files = sorted(files, key=lambda x: datetime.datetime.strptime(x[:10], '%Y-%m-%d'))
dfs = pl.DataFrame()
with alive_bar() as bar:
    for f in files:
        fp = os.path.join(diri, f)
        try:
            df = l1_l2_df_from_tle_file(fp)
        except pl.exceptions.ComputeError as e:
            print(f)
            raise e

        if 'TLE_LINE1' not in df:
            continue

        # print(dict(year=f[11:15], month=int(f[16:18]), day=int(f[19:21])))
        # drop_epochs_after_or_equal_to = pl.date(year=int(f[11:15]), month=int(f[16:18]), day=int(f[19:21]))
        df = process_df(df)
        df.shrink_to_fit(in_place=True)
        dfs.vstack(df, in_place=True)
        bar(df.height)

print("Writing df to parquet")
t1 = time.time()
dfs.lazy().sink_parquet(f'database/noice_by_date.parquet', compression='lz4')

print(time.time()-t1)

