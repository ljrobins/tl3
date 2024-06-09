import os
import polars as pl
from tqdm import tqdm
import concurrent.futures
import time
import datetime
from typing import Tuple
import numpy as np
import difflib

def print_str_differences(a: str, b: str) -> None:
    for i,s in enumerate(difflib.ndiff(a, b)):
        if s[0]==' ': 
            continue
        elif s[0]=='-':
            print(u'Delete "{}" from position {}'.format(s[-1],i))
        elif s[0]=='+':
            print(u'Add "{}" to position {}'.format(s[-1],i))    


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
    day_of_year = tle['EPOCH'].timetuple().tm_yday
    day_fraction = tle['EPOCH'].hour / 24 + tle['EPOCH'].minute / (24 * 60) + tle['EPOCH'].second / (24 * 3600) + tle['EPOCH'].microsecond / (24 * 3600 * 1e6)
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


def implied_decimal_to_float(s: str) -> float:
    if not len(s.strip()):
        return 0.0
    else:
        return float(f'{s[0]}0.{s[1:6].strip()}') * 10**(int(s[-2:]))

def file_of_tles(f: str, src: str) -> pl.DataFrame:
    global df
    print(f"Creating DataFrame for {f}")
    tles = []
    i = 0
    with open(f, 'r') as fp:
        for l in fp:
            l = l.strip('\n')
            if not len(l):
                continue
            try:
                if l[:2] == '1 ':
                    l1 = l
                    if len(l) < 69:
                        print(f"line {l} too short, skipping...")
                        continue

                    tle = {}
                    tle['NORAD_CAT_ID'] = int(l[2:7])
                    tle['INTL_DES'] = l[9:17].strip().replace(' ', '')
                    # tle['CLASSIFICATION'] = l[7]
                    year = int(f'20{l[18:20]}') if int(l[18:20]) < 50 else int(f'19{l[18:20]}')
                    days = float(l[20:32])
                    tle['EPOCH'] = datetime.datetime(year, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(days=days-1)
                    tle['N_DOT'] = float(l[33:43]) # first derivative of the mean motion (ballistic coefficent)
                    tle['N_DDOT'] = implied_decimal_to_float(l[44:52]) # second derivative of the mean motion
                    tle['B_STAR'] = implied_decimal_to_float(l[53:61])
                    tle['ELSET_NUM'] = int(l[64:68])
                    tle['CHECKSUM1'] = int(l[68])
                elif l[:2] == '2 ':
                    if len(l) < 69:
                        print(f"line {l} too short, skipping...")
                        continue

                    l2 = l
                    tle['INC'] = float(l[8:16])
                    tle['RAAN'] = float(l[17:25])
                    tle['ECC'] = float(f'0.{l[26:33]}')
                    tle['AOP'] = float(l[34:42])
                    tle['MA'] = float(l[43:51])
                    tle['N'] = float(l[52:63]) # mean motion, revs/day
                    tle['REV_NUM'] = int(l[63:68]) if len(l[63:68].strip()) or ' ' in l[63:68].strip() else -1
                    try:
                        tle['CHECKSUM2'] = int(l[68])
                    except IndexError as e:
                        tle['CHECKSUM2'] = 0
                    i += 1
                    tles.append(tle)
            except ValueError as e:
                print(e)
                print(l)
                print(f)
                pass
    df = pl.DataFrame(tles).cast({pl.Int64: pl.Int32, pl.Float64: pl.Float32})
    if "ELSET_NUM" in df.columns:
        df = df.cast({
                      "CHECKSUM1": pl.UInt8, 
                      "CHECKSUM2": pl.UInt8, 
                      "ELSET_NUM": pl.UInt16})
    df = df.with_columns(
        pl.lit(src).alias('SOURCE')
    )
    return df.sort(['NORAD_CAT_ID', 'EPOCH'])

def build_df(name):
    executor = concurrent.futures.ProcessPoolExecutor(8)

    dirs = [
            # ('data_pl', 'P'),
            ('data_st', 'N'),
            # ('data_45', 'J'), 
            # ('data_bg', 'B'), 
            # ('data_bg/old_tles', 'B'),
            ]

    t1 = time.time()
    df = pl.DataFrame()
    futures = []
    for diri,src in dirs:
        files = [x for x in os.listdir(diri) if os.path.getsize(os.path.join(diri, x))]
        files = sorted(files, key=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d.txt'))
        for f in files:
            if not os.path.isdir(os.path.join(diri, f)):
                futures.append(executor.submit(file_of_tles, os.path.join(diri, f), src))
        
    concurrent.futures.wait(futures)
    executor.shutdown(False)
    print(f"Create times {time.time()-t1}")

    for f in tqdm(futures, desc="Stacking dfs"):
        res = f.result()
        if res.width > 1:
            df = df.vstack(res)
        del res  

    print("Writing df to parquet")
    t1 = time.time()
    lf = df.lazy()
    lf = lf.unique(subset=['EPOCH', 'N', 'ECC', 'INC', 'AOP', 'RAAN', 'MA'])
    
    lf = lf.sort(['NORAD_CAT_ID', 'EPOCH'])
    lf.sink_parquet(f'database/{name}_by_norad.parquet', compression='lz4', row_group_size=int(2e5))
    
    lf = lf.sort(['EPOCH', 'NORAD_CAT_ID'])
    lf.sink_parquet(f'database/{name}_by_date.parquet', compression='lz4', row_group_size=int(2e5))

    print(time.time()-t1)
