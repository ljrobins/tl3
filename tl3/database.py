import os
import polars as pl
import time
import datetime
from typing import Tuple, Union, List
import numpy as np
import duckdb
from alive_progress import alive_bar
from .query import get_tle_file_list, get_tle_file_list_as_dates

DT_REF = datetime.datetime(1958, 1, 1, tzinfo=datetime.timezone.utc)


def _float_to_implied_decimal_point(v: float) -> str:
    p = int(f'{v:e}'[-3:])
    if p != 0:
        p += 1
    else:
        p = -0.0
    m = f'{round(v * 10 ** (-p+5)):+06}'
    m = m.replace('+', ' ')
    return f'{m}{p:+.0f}'


def _tle_to_l1(tle) -> str:
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
    b_star = _float_to_implied_decimal_point(tle['B_STAR'])
    l1_ = f"1 {tle['NORAD_CAT_ID']:05d}U {tle['INTL_DES'].ljust(8, ' ')} {year_last_two}{day_of_year}{day_fraction_str.lstrip('0')} {n_dot} {_float_to_implied_decimal_point(tle['N_DDOT'])} {b_star} 0 {str(tle['ELSET_NUM']).rjust(4, ' ')}{tle['CHECKSUM1']}"
    return l1_


def _tle_to_l2(tle) -> str:
    ecc = f"{tle['ECC']:>08.7f}"
    ecc = ecc[2:]
    n = f"{tle['N']:>011.8f}"
    l2_ = f"2 {tle['NORAD_CAT_ID']:05d} {tle['INC']:>08.4f} {tle['RAAN']:>08.4f} {ecc} {tle['AOP']:>08.4f} {tle['MA']:>08.4f} {n}{tle['REV_NUM']:>5}{tle['CHECKSUM2']}"
    return l2_


def _df_row_to_tle(tle) -> Tuple[str, str]:
    l1_ = _tle_to_l1(tle)
    l2_ = _tle_to_l2(tle)
    return (l1_, l2_)


def _build_df_from_files(file_paths: list[str]) -> pl.DataFrame:
    dfs = pl.DataFrame()
    with alive_bar() as bar:
        for f in file_paths:
            try:
                df = _l1_l2_df_from_tle_file(f)
            except pl.exceptions.ComputeError as e:
                print(f)
                raise e

            if 'TLE_LINE1' not in df:
                continue

            df = _process_df(f, df)
            df.shrink_to_fit(in_place=True)
            dfs.vstack(df, in_place=True)
            bar(df.height)
    return dfs


def _build_df_from_scratch(tle_dir: str, save_path: str) -> None:
    files = get_tle_file_list(tle_dir)
    df = _build_df_from_files(files)

    _save_df_to_parquet(df, save_path)


def _append_new_tles_to_df(tle_dir: str, save_path: str) -> None:
    max_date = (
        duckdb.sql(
            f"""
        SELECT max(EPOCH) FROM {repr(save_path)}
        """
        )
        .fetchone()[0]
        .date()
    )

    files = get_tle_file_list(tle_dir)
    dates = get_tle_file_list_as_dates(tle_dir)

    unused_files = []

    for f, d in zip(files, dates):
        if d[1] > max_date:
            unused_files.append(f)

    if len(unused_files):
        df = _build_df_from_files(unused_files)

        duckdb.sql(f"""
            CREATE TABLE all_tles AS SELECT * FROM {repr(save_path)};
            INSERT INTO all_tles SELECT * FROM df;
        """)

        _save_df_to_parquet(df_or_duckdb_table_name='all_tles', save_path=save_path)

        print(f'Appended {df.height} TLEs to the master database!')
    else:
        print("No new TLEs to append to the master database")


def _save_df_to_parquet(
    df_or_duckdb_table_name: str | pl.DataFrame, save_path: str
) -> None:
    print(f'Writing to parquet at {save_path}...')
    t1 = time.time()

    if isinstance(df_or_duckdb_table_name, pl.DataFrame):
        duckdb.sql(f"""
            COPY
                (SELECT * FROM df_or_duckdb_table_name)
                TO {repr(save_path)}
                (FORMAT 'parquet', COMPRESSION 'lz4');
        """)
    else:  # then it's a duckdb table name
        duckdb.sql(f"""
            COPY
                (SELECT * FROM {df_or_duckdb_table_name})
                TO {repr(save_path)}
                (FORMAT 'parquet', COMPRESSION 'lz4');
        """)

    print(f'Writing to parquet took {time.time() - t1:.1f} seconds')


def build_parquet(
    tle_dir: str = None, parquet_dir: str = None, from_scratch: bool = False
) -> None:
    """Builds and saves a parquet file from all the TLE files (ending in .txt) in the target directory

    :param tle_dir: Target directory to search for TLEs, defaults to None (uses the default internal location ./txt/)
    :type tle_dir: str, optional
    :param parquet_dir: Directory to save the parquet file to, defaults to None (uses the default internal location ./processed/)
    :type parquet_dir: str, optional
    :param from_scratch: Whether to build the dataframe from scratch (necessary if the schema changes) or to append new TLEs, defaults to False
    :type from_scratch: bool, optional
    :raises pl.exceptions.ComputeError: If an error occurs within polars while parsing the TLE file
    """
    tle_dir = os.environ['TL3_TXT_DIR'] if tle_dir is None else tle_dir

    save_path = (
        os.environ['TL3_DB_PATH']
        if parquet_dir is None
        else os.path.join(parquet_dir, 'twoline.parquet')
    )

    if from_scratch:
        _build_df_from_scratch(tle_dir, save_path)
    else:
        _append_new_tles_to_df(tle_dir, save_path)


def tles_between(
    date_start: datetime.datetime,
    date_end: datetime.datetime,
    norad_cat_id: Union[int, str] = 'all',
    cols: Union[List[str], str] = '*',
    return_as: str = 'polars',
) -> Union[pl.DataFrame, duckdb.duckdb.DuckDBPyRelation, np.ndarray]:
    """

    :param date_start: Start datetime for the query, in UTC
    :type date_start: datetime.datetime
    :param date_end: End datetime for the query, in UTC
    :type date_end: datetime.datetime
    :param norad_cat_id: NORAD ID to query for (either a single int or "all"), defaults to 'all'
    :type norad_cat_id: Union[int, str], optional
    :param cols: SQL-style selectors for column names. Either a list of strings (ex. ``["EPOCH", "INC"]``), or ``"*"`` for all columns, defaults to ``"*"``
    :type cols: Union[List[str], str], optional
    :param return_as: Format to return results as. "duck" returns the raw duckdb query result, "polars" returns a polars DataFrame, and "tle" returns a numpy string [nx2] array, defaults to "polars"
    :type return_as: string, optional
    """

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
            l1s[i], l2s[i] = _df_row_to_tle(row)
        return np.vstack((l1s, l2s)).T
    else:
        return x


def _l1_l2_df_from_tle_file(fpath: str) -> pl.DataFrame:
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


def _implied_decimal_to_float(s: pl.Series) -> pl.Expr:
    # s is a pl.col(col_name).str.slice(start, length) instance
    return (
        s.str.head(5).str.strip_chars().str.to_integer(strict=False)
        * (10.0**-4)
        * 10.0 ** s.str.tail(2).str.to_integer(strict=False)
    )


def _process_df(fpath: str, df: pl.DataFrame) -> pl.DataFrame:
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
        _implied_decimal_to_float(df['TLE_LINE1'].str.slice(44, 8))
        .cast(pl.Float32)
        .alias('N_DDOT'),
        _implied_decimal_to_float(df['TLE_LINE1'].str.slice(53, 8))
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
    ).drop('EPOCH_DAY', 'EPOCH_YEAR')

    height_before_drops = df.height
    df = df.drop('TLE_LINE1', 'TLE_LINE2', 'index').drop_nulls()

    if height_before_drops - df.height > 0:
        print(
            f'{fpath}: failed to parse {height_before_drops-df.height} rows (out of {height_before_drops})'
        )

    df = df.sort(['EPOCH', 'NORAD_CAT_ID'])
    return df
