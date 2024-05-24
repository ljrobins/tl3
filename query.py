import asyncio
from asynciolimiter import Limiter
import dotenv
import os
import datetime as dt
from spacetrack import SpaceTrackClient
import dotenv
dotenv.load_dotenv('.env.secret')
import time
import socket
import httpx

rate_limiter = Limiter(200/3600) # <300 requests / hour

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

def get_tles_between(
    st: SpaceTrackClient,
    dtimes: list[dt.datetime],
) -> list[tuple[str, str]]:
    """Gets all TLEs published in the range of datetimes passed

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
        "format": 'tle',
        'iter_lines': True,
    }
    tles = st.tle(**query)
    cat_name = f'{idstr}.txt'
    save_fpath = os.path.join('data', cat_name)

    with open(save_fpath, 'a') as f:
        f.writelines('\n'.join(tles))

    return tles

async def request(dt_start: dt.datetime, dt_end: dt.datetime, st: SpaceTrackClient):
    success = False
    while not success:
        try:
            await rate_limiter.wait() # Wait for a slot to be available.
            print(f'Querying TLEs for {dt_start}...')    
            get_tles_between(st, [dt_start, dt_end])
            success = True
        except httpx.ConnectError:
            assert not internet()
            while not internet():
                print("No internet! waiting for connection...")
                time.sleep(10)
        except httpx.ReadTimeout:
            print("Read timeout... retrying this query")


async def main():
    dotenv.load_dotenv('.env.secret')
    httpx_client = httpx.Client(timeout=None)
    st = SpaceTrackClient(os.environ['SPACETRACK_USERNAME'], 
                            os.environ['SPACETRACK_PASSWORD'], httpx_client=httpx_client)

    coros = []

    start_day = dt.datetime(2024, 4, 20)
    end_day = dt.datetime(2020, 1, 1)
    total_days = int((start_day - end_day).total_seconds() / 86400)
    dates = [start_day - dt.timedelta(days=deltat) for deltat in range(total_days)]
    for s,e in zip(dates[1:], dates[:-1]):
        coros.append(request(s,e,st))
    await asyncio.gather(*coros)


asyncio.run(main())