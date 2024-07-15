import os
import polars as pl
import time
import datetime
from typing import Tuple, Union, List
import numpy as np
import duckdb
from alive_progress import alive_bar

DT_REF = datetime.datetime(1958, 1, 1, tzinfo=datetime.timezone.utc)


def float_to_implied_decimal_point(v: float) -> str:
    p = int(f'{v:e}'[-3:])
    if p != 0:
        p += 1
    else:
        p = -0.0
    m = f'{round(v * 10 ** (-p+5)):+06}'
    m = m.replace('+', ' ')
    return f'{m}{p:+.0f}'


def tle_to_l1(tle) -> str:
    day_of_year = f"{tle['EPOCH'].timetuple().tm_yday-1:03}"
    day_fraction = (
        tle['EPOCH'].hour / 24
        + tle['EPOCH'].minute / (24 * 60)
        + tle['EPOCH'].second / (24 * 3600)
        + tle['EPOCH'].microsecond / (24 * 3600 * 1e6)
    )
    year_last_two = str(tle['EPOCH'].year)[2:]
    day_fraction_str = f'{day_fraction:.8f}'
    n_dot = f"{tle['N_DOT']:+.8f}"
    n_dot = (n_dot[:1] + n_dot[2:]).replace('+', ' ')
    b_star = float_to_implied_decimal_point(tle['B_STAR'])
    l1_ = f"1 {tle['NORAD_CAT_ID']:05d}U {tle['INTL_DES'].ljust(8, ' ')} {year_last_two}{day_of_year}{day_fraction_str.lstrip('0')} {n_dot} {float_to_implied_decimal_point(tle['N_DDOT'])} {b_star} 0 {str(tle['ELSET_NUM']).rjust(4, ' ')}{tle['CHECKSUM1']}"
    return l1_


def tle_to_l2(tle) -> str:
    ecc = f"{tle['ECC']:>08.7f}"
    ecc = ecc[2:]
    n = f"{tle['N']:>011.8f}"
    l2_ = f"2 {tle['NORAD_CAT_ID']:05d} {tle['INC']:>08.4f} {tle['RAAN']:>08.4f} {ecc} {tle['AOP']:>08.4f} {tle['MA']:>08.4f} {n}{tle['REV_NUM']:>5}{tle['CHECKSUM2']}"
    return l2_


def df_row_to_tle(tle) -> Tuple[str, str]:
    l1_ = tle_to_l1(tle)
    l2_ = tle_to_l2(tle)
    return (l1_, l2_)


def build_parquet(target_dir: str = None, parquet_dir: str = None) -> None:
    """Builds and saves a parquet file from all the TLE files (ending in .txt) in the target directory

    :param target_dir: Target directory to search, defaults to None (uses the default internal location ./txt/)
    :type target_dir: str, optional
    :param parquet_dir: Directory to save the parquet file to, defaults to None (uses the default internal location ./processed/)
    :type parquet_dir: str, optional
    :raises pl.exceptions.ComputeError: If an error occurs within polars while parsing the TLE file
    """
    txt_dir = os.environ['TL3_TXT_DIR'] if target_dir is None else target_dir

    files = [
        x
        for x in os.listdir(txt_dir)
        if os.path.getsize(os.path.join(txt_dir, x)) and x.endswith('.txt')
    ]
    files = sorted(files, key=lambda x: datetime.datetime.strptime(x[:10], '%Y-%m-%d'))
    dfs = pl.DataFrame()
    with alive_bar() as bar:
        for f in files:
            fp = os.path.join(txt_dir, f)
            try:
                df = l1_l2_df_from_tle_file(fp)
            except pl.exceptions.ComputeError as e:
                print(f)
                raise e

            if 'TLE_LINE1' not in df:
                continue

            df = process_df(f, df)
            df.shrink_to_fit(in_place=True)
            dfs.vstack(df, in_place=True)
            bar(df.height)

    save_path = (
        os.environ['TL3_DB_PATH']
        if parquet_dir is None
        else os.path.join(parquet_dir, 'twoline.parquet')
    )
    print(f'Writing df to parquet at {save_path}...')
    t1 = time.time()
    dfs.lazy().sink_parquet(save_path, compression='lz4')
    print(f'Writing df to parquet took {time.time() - t1:.1f} seconds')


def tles_between(
    date_start: datetime.datetime,
    date_end: datetime.datetime,
    norad_cat_id: Union[int, str] = 'all',
    cols: List[str] = '*',
    return_as: str = 'polars',
):
    assert return_as.lower() in [
        'polars',
        'tle',
        'duck',
    ], "return_as must be 'polars', 'duck', or 'tle'"
    assert date_end > date_start, 'date_start must be before date_end'
    norad_cat_id = str(norad_cat_id)
    if norad_cat_id.lower() != 'all':
        assert int(norad_cat_id) < 1e5, 'norad_cat_id must be < 100_000'

    idstr, fdstr = date_start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d')
    constraints = []
    constraints.append(f'EPOCH BETWEEN {repr(idstr)} AND {repr(fdstr)}')
    if norad_cat_id.lower() != 'all' and norad_cat_id.isdigit():
        constraints.append(f'NORAD_CAT_ID=={norad_cat_id}')

    db = os.path.join(os.environ['TL3_DIR'], 'processed', 'twoline.parquet')

    if isinstance(cols, list):
        col_repr = ', '.join(cols)
    elif isinstance(cols, str):
        col_repr = cols
    else:
        raise NotImplementedError('cols must be of type list or str')

    query_str = f"""
        SELECT {col_repr}
        FROM {repr(db)}
        {'WHERE ' + ' AND '.join(constraints)}
        ORDER BY EPOCH ASC;
        """
    x = duckdb.sql(query_str)

    if return_as.lower() == 'polars':
        return x.pl()
    elif return_as.lower() == 'tle':
        x = x.pl()
        l1s = np.zeros(x.height, dtype='<U69')
        l2s = np.zeros(x.height, dtype='<U69')
        for i, row in enumerate(x.iter_rows(named=True)):
            l1s[i], l2s[i] = df_row_to_tle(row)
        return np.vstack((l1s, l2s)).T
    else:
        return x


def l1_l2_df_from_tle_file(fpath: str) -> pl.DataFrame:
    df = pl.read_csv(fpath, has_header=False)
    df = df.with_row_index()
    df = df.with_columns(
        pl.when(pl.col('column_1').str.head(1) == '1')
        .then(1)
        .otherwise(2)
        .alias('line_num'),
        pl.col('index') // 2,
    )
    bad_inds = (
        df['line_num'].shift(fill_value=2)
        + df['line_num'].shift(n=-1, fill_value=1)
        - df['line_num']
    ) != 1
    df = df.filter(bad_inds)

    df = df.pivot(index='index', on='line_num', values='column_1')
    df = df.rename(
        {
            '1': 'TLE_LINE1',
            '2': 'TLE_LINE2',
        }
    )
    return df


def implied_decimal_to_float(s: pl.Series) -> pl.Expr:
    # s is a pl.col(col_name).str.slice(start, length) instance
    return (
        s.str.head(5).str.strip_chars().str.to_integer(strict=False)
        * (10.0**-4)
        * 10.0 ** s.str.tail(2).str.to_integer(strict=False)
    )


def process_df(fpath: str, df: pl.DataFrame) -> pl.DataFrame:
    df = df.filter(
        (pl.col('TLE_LINE1').str.len_chars() == 69),
        (pl.col('TLE_LINE2').str.len_chars() == 69),
    )
    df = df.with_columns(
        pl.col('TLE_LINE1')
        .str.slice(2, 5)
        .str.strip_chars()
        .cast(pl.UInt32)
        .alias('NORAD_CAT_ID'),
        pl.col('TLE_LINE1')
        .str.slice(9, 8)
        .str.strip_chars()
        .str.replace_all(' ', '')
        .alias('INTL_DES'),
        pl.col('TLE_LINE1')
        .str.slice(18, 2)
        .str.strip_chars()
        .cast(pl.Int16)
        .alias('EPOCH_YEAR'),
        pl.col('TLE_LINE1')
        .str.slice(20, 12)
        .str.strip_chars()
        .cast(pl.Float64)
        .alias('EPOCH_DAY'),
        pl.col('TLE_LINE1')
        .str.slice(33, 10)
        .str.strip_chars()
        .cast(pl.Float32)
        .alias('N_DOT'),
        implied_decimal_to_float(df['TLE_LINE1'].str.slice(44, 8))
        .cast(pl.Float32)
        .alias('N_DDOT'),
        implied_decimal_to_float(df['TLE_LINE1'].str.slice(53, 8))
        .cast(pl.Float32)
        .alias('B_STAR'),
        pl.col('TLE_LINE1')
        .str.slice(64, 4)
        .str.strip_chars()
        .cast(pl.UInt16)
        .alias('ELSET_NUM'),
        pl.col('TLE_LINE1').str.slice(68, 1).cast(pl.UInt8).alias('CHECKSUM1'),
        pl.col('TLE_LINE2')
        .str.slice(8, 7)
        .str.strip_chars()
        .cast(pl.Float32, strict=False)
        .alias('INC'),
        pl.col('TLE_LINE2')
        .str.slice(17, 7)
        .str.strip_chars()
        .cast(pl.Float32, strict=False)
        .alias('RAAN'),
        (
            pl.col('TLE_LINE2')
            .str.slice(26, 7)
            .str.strip_chars()
            .cast(pl.Float32, strict=False)
            * 10.0**-7
        ).alias('ECC'),
        pl.col('TLE_LINE2')
        .str.slice(34, 7)
        .str.strip_chars()
        .cast(pl.Float32, strict=False)
        .alias('AOP'),
        pl.col('TLE_LINE2')
        .str.slice(43, 7)
        .str.strip_chars()
        .cast(pl.Float32, strict=False)
        .alias('MA'),
        pl.col('TLE_LINE2')
        .str.slice(52, 10)
        .str.strip_chars()
        .cast(pl.Float32, strict=False)
        .alias('N'),  # mean motion, revs/day
        pl.col('TLE_LINE2')
        .str.slice(63, 4)
        .str.replace_all(' ', '0')
        .cast(pl.UInt16, strict=False)
        .alias('REV_NUM'),
        pl.col('TLE_LINE2').str.slice(68, 1).cast(pl.UInt8).alias('CHECKSUM2'),
    )
    df = df.with_columns(
        pl.when(pl.col('EPOCH_YEAR') > 50)
        .then(1900 + pl.col('EPOCH_YEAR'))
        .otherwise(2000 + pl.col('EPOCH_YEAR'))
        .alias('EPOCH_YEAR'),
    )
    df = df.with_columns(
        pl.from_epoch(
            pl.datetime(
                year=pl.col('EPOCH_YEAR'), month=1, day=1, time_unit='ms'
            ).dt.epoch('ms')
            + pl.col('EPOCH_DAY') * 86400 * 1e3,
            time_unit='ms',
        ).alias('EPOCH')
    )

    height_before_drops = df.height
    df = df.drop('TLE_LINE1', 'TLE_LINE2', 'index').drop_nulls()

    if height_before_drops - df.height > 0:
        print(
            f'{fpath}: failed to parse {height_before_drops-df.height} rows (out of {height_before_drops})'
        )

    df = df.sort(['EPOCH', 'NORAD_CAT_ID'])
    return df
