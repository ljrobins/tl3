import asyncio
from asynciolimiter import Limiter
import dotenv
import os
import datetime as dt
from spacetrack import SpaceTrackClient
import time
import socket
import httpx

rate_limiter = Limiter(290/3600) # <300 requests / hour

def internet(host: str = "8.8.8.8", port: int = 53, timeout: int = 3):
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

def query_tles_between(
    st: SpaceTrackClient,
    dtimes: list[dt.datetime],
    save_dir: str = None,
    endpoint: str = 'tle'
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
        f"{'publish_' if endpoint == 'tle_publish' else ''}epoch": f"{idstr}--{fdstr}",
        "format": 'tle',
        'iter_lines': True,
    }

    tles = getattr(st, endpoint)(**query)
    cat_name = f'{idstr} {fdstr}.txt'
    save_fpath = os.path.join(save_dir, cat_name)

    with open(save_fpath, 'w') as f:
        f.writelines('\n'.join(tles))

    return tles

async def request(dt_start: dt.datetime, dt_end: dt.datetime, st: SpaceTrackClient, save_dir: str = None, endpoint: str = 'tle'):
    success = False
    while not success:
        try:
            await rate_limiter.wait() # Wait for a slot to be available.
            print(f'Querying TLEs for {dt_start} -- {dt_end}...')    
            query_tles_between(st, [dt_start, dt_end], save_dir=save_dir, endpoint=endpoint)
            success = True
        except httpx.ConnectError:
            assert not internet()
            while not internet():
                print("No internet! waiting for connection...")
                time.sleep(10)
        except httpx.ReadTimeout:
            print("Read timeout... retrying this query")


async def _save_tles(dates: list[dt.datetime], save_dir: str = None, endpoint: str = 'tle'):
    httpx_client = httpx.Client(timeout=None)
    st = SpaceTrackClient(os.environ['SPACETRACK_USERNAME'], 
                            os.environ['SPACETRACK_PASSWORD'], httpx_client=httpx_client)

    coros = []
    for s,e in zip(dates[1:], dates[:-1]):
        coros.append(request(s,e,st,save_dir,endpoint))
    await asyncio.gather(*coros)

def save_tles(dates: list[dt.datetime], save_dir: str = None, endpoint: str = 'tle'):
    """Dates increasing please thanks

    :param dates: _description_
    :type dates: list[dt.datetime]
    """
    asyncio.run(_save_tles(dates, save_dir=save_dir, endpoint=endpoint))