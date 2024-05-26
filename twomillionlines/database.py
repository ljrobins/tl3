import os
import polars as pl
from tqdm import tqdm
import concurrent.futures
import time
import datetime

def implied_decimal_to_float(s: str) -> float:
    return float(f'{s[0]}0.{s[1:6].strip()}') * 10**(int(s[-2:]))

def day_of_tles(f: str) -> pl.DataFrame:
    global df
    print(f"Creating DataFrame for {f}")
    tles = []
    with open(os.path.join('data', f), 'r') as fp:
        for l in fp:
            try:
                if l[0] == '1':
                    tle = {}
                    tle['NORAD_CAT_ID'] = int(l[2:7])
                    # tle['CLASSIFICATION'] = l[7]
                    tle['INTL_DES'] = l[9:17].strip()
                    year = int(f'20{l[18:20]}') if int(l[18:20]) < 50 else int(f'19{l[18:20]}')
                    days = float(l[20:32])
                    tle['EPOCH'] = datetime.datetime(year, 1,1, tzinfo=datetime.timezone.utc) + datetime.timedelta(days=days)
                    tle['N_DOT'] = float(l[33:43]) # first derivative of the mean motion (ballistic coefficent)
                    tle['N_DDOT'] = implied_decimal_to_float(l[44:52]) # second derivative of the mean motion
                    tle['B_STAR'] = implied_decimal_to_float(l[53:61])
                    tle['ELSET_NUM'] = int(l[64:68])
                    # tle['CHECKSUM'] = int(l[68])
                elif l[0] == '2':
                    tle['INC'] = float(l[8:16])
                    tle['RAAN'] = float(l[17:25])
                    tle['ECC'] = float(f'0.{l[26:33]}')
                    tle['AOP'] = float(l[34:42])
                    tle['MA'] = float(l[43:51])
                    tle['N'] = float(l[52:63]) # mean motion, revs/day
                    tle['REV_NUM'] = int(l[63:68])
                    tles.append(tle)
            except ValueError as e:
                print(e)
                print(l)
                print(f)
                pass
    df = pl.DataFrame(tles).cast({pl.Int64: pl.Int32, pl.Float64: pl.Float32})
    if "ELSET_NUM" in df.columns:
        df = df.cast({
            # "EPOCH_YEAR": pl.UInt16, 
                    #   "CHECKSUM": pl.UInt8, 
                      "ELSET_NUM": pl.UInt16})
    return df.unique()

def build_df(name):
    executor = concurrent.futures.ProcessPoolExecutor(8)

    files = os.listdir('data')

    t1 = time.time()
    df = pl.DataFrame()
    futures = []
    for f in files:
        futures.append(executor.submit(day_of_tles, f))
    
    concurrent.futures.wait(futures)
    executor.shutdown(False)
    print(f"Create times {time.time()-t1}")

    for f in tqdm(futures, desc="Stacking dfs"):
        res = f.result()
        if res.width > 0:
            df = df.vstack(res)
        del res  

    print("Writing df to parquet")
    t1 = time.time()
    lf = pl.LazyFrame(df).unique()
    lf.sink_parquet(f'database/{name}.parquet', compression='lz4')
    print(time.time()-t1)

def get_df():
    return pl.read_parquet(os.path.join(os.environ["TLE_DIR"], '..', 'database', 'db_all.parquet'))