import asyncio
from asynciolimiter import Limiter
import dotenv
import os
import datetime as dt
from spacetrack import SpaceTrackClient
import dotenv
dotenv.load_dotenv('.env.secret')
import json
import polars as pl
from typing import Tuple
import time
import socket
import httpx

rate_limiter = Limiter(298/3600) # <300 requests / hour

def internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False


def make_sync_st_request(st, query, endpoint: str = "tle"):
    return getattr(st, endpoint)(**query)


def get_tles_between(
    st: SpaceTrackClient,
    satnum: int,
    dtimes: list[dt.datetime],
) -> list[tuple[str, str]]:
    """Gets all TLEs published in the range of datetimes passed

    :param satnum: Satellite number, ex. 25544 for ISS ZARYA
    :type satnum: int
    :param dtimes: Datetimes, assumed to be UTC, in chronologically ascending order
    :type dtimes: np.ndarray[datetime]
    :raises ValueError: If the object decays during the timespan
    :return: List of TLE lines 1 and 2
    :rtype: list[tuple[str, str]]
    """
    idtime, fdtime = dtimes[0], dtimes[-1]
    idstr, fdstr = idtime.strftime("%Y-%m-%d"), fdtime.strftime("%Y-%m-%d")
    query = {
        "orderby": "epoch asc",
        "epoch": f"{idstr}--{fdstr}",
        "norad_cat_id": str(satnum),
        "format": 'tle',
        'iter_lines': True,
    }

    # Get the closest TLE to the specified date
    tles = make_sync_st_request(st, query)
    cat_name = f'{satnum}.txt'
    save_fpath = os.path.join('data', cat_name)

    with open(save_fpath, 'a') as f:
        f.writelines('\n'.join(tles))

    return tles

async def request(satnum: int, dt_start: dt.datetime, dt_end: dt.datetime, st: SpaceTrackClient):
    try:
        await rate_limiter.wait() # Wait for a slot to be available.
        print(f'Querying TLEs for {satnum} from {dt_start} to {dt_end}...')    
        get_tles_between(st, satnum, [dt_start, dt_end])
    except httpx.ConnectError as e:
        assert not internet()
        while not internet():
            print("No internet! waiting for connection...")
            time.sleep(10)


async def main(st: SpaceTrackClient, launch_decay_df):
    coros = []
    max_days_per_request = 50000.0
    for cat_id, launch_date, decay_date, total_days in launch_decay_df.iter_rows():
        if total_days > max_days_per_request:
            iters_needed = int(total_days / max_days_per_request) + 1
            dts = [launch_date + dt.timedelta(days=i * max_days_per_request) for i in range(iters_needed)]
            dts.append(decay_date)
        else:
            dts = [launch_date, decay_date]

        assert dts[-1] >= decay_date
        assert dts[0] <= launch_date
        coros.extend(request(cat_id,s,e,st) for s,e in zip(dts[:-1],dts[1:]))

    await asyncio.gather(*coros)

dotenv.load_dotenv('.env.secret')
st = SpaceTrackClient(os.environ['SPACETRACK_USERNAME'], 
                        os.environ['SPACETRACK_PASSWORD'])

def get_all_decays(st: SpaceTrackClient):
    res = st.decay(decay_epoch='>1950-01-01', format='json')
    res_str = json.loads(res)
    with open('util/decay.json', 'w') as f:
        json.dump(res_str, f)


def get_all_launches(st: SpaceTrackClient):
    res = st.satcat(launch='>1950-01-01', format='json')
    res_str = json.loads(res)
    with open('util/launch.json', 'w') as f:
        json.dump(res_str, f)

# get_all_decays(st)
# get_all_launches(st)

def load_launch_decay_dfs() -> Tuple[pl.DataFrame, pl.DataFrame]:
    decay = pl.read_json('util/decay.json')
    launch = pl.read_json('util/launch.json')

    launch = launch.with_columns(
    pl.col("LAUNCH").str.to_datetime("%Y-%m-%d"),
    pl.col("NORAD_CAT_ID").str.to_integer(),
    )

    decay = decay.with_columns(
    pl.col("DECAY_EPOCH").str.to_datetime("%Y-%m-%d %H:%M:%S"),
    pl.col("NORAD_CAT_ID").str.to_integer(),
    )

    return launch, decay

def get_cat_id_launch_decay_dates(launch: pl.DataFrame, decay: pl.DataFrame, norad_cat_id: int) -> Tuple[dt.datetime, dt.datetime]:
    li = launch.select(
        pl.arg_where(pl.col("NORAD_CAT_ID") == norad_cat_id)
    ).to_series().to_list()
    if len(li) == 1:
        launch_date = launch["LAUNCH"][li[0]]
    else:
        launch_date = dt.datetime.today()

    di = decay.select(
        pl.arg_where(pl.col("NORAD_CAT_ID") == norad_cat_id)
    ).to_series().to_list()
    if len(di) == 1:
        decay_date = decay["DECAY_EPOCH"][di[0]]
    else:
        decay_date = dt.datetime.today()

    return launch_date, decay_date

def get_dates_df() -> pl.DataFrame:
    launch, decay = load_launch_decay_dfs()

    max_norad_id = launch['NORAD_CAT_ID'][launch["LAUNCH"].arg_max()]

    rows = []
    for norad_cat_id in range(58, 100):
        ldate, ddate = get_cat_id_launch_decay_dates(launch, decay, norad_cat_id)
        days_alive = (ddate-ldate).total_seconds() / 86400
        rows.append({"NORAD_CAT_ID": norad_cat_id, "LAUNCH_DATE": ldate, "DECAY_DATE": ddate, "DAYS_ALIVE": days_alive})

    return pl.DataFrame(rows)

launch_decay_df = get_dates_df()

asyncio.run(main(st, launch_decay_df))