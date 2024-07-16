import asyncio
from asynciolimiter import Limiter
import os
import datetime
from spacetrack import SpaceTrackClient
from spacetrack.base import AuthenticationError
import time
import socket
import httpx
from dotenv import load_dotenv
from itertools import pairwise
import ssl
import shutil
import gzip
import urllib.request

rate_limiter = Limiter(
    290 / 3600
)  # < 300 requests / hour to not make space-track upset


def _get_spacetrack_client(username=None, password=None) -> SpaceTrackClient:
    return SpaceTrackClient(
        os.environ['SPACETRACK_USERNAME'] if username is None else username,
        os.environ['SPACETRACK_PASSWORD'] if password is None else password,
        httpx_client=httpx.Client(timeout=None),
    )


def _internet(host: str = '8.8.8.8', port: int = 53, timeout: int = 3):
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


def _query_tles_between(
    st: SpaceTrackClient,
    dates: list[datetime.date],
    save_path: str = None,
    endpoint: str = 'tle',
) -> list[tuple[str, str]]:
    """Gets all TLEs published in the range of datetimes passed

    :param st: SpaceTrackClient class instance to make the query
    :type st: SpaceTrackClient
    :param dates: Datetimes, assumed to be UTC, in chronologically ascending order
    :type dates: np.ndarray[datetime]
    :raises ValueError: If the object decays during the timespan
    :return: List of TLE lines 1 and 2
    :rtype: list[tuple[str, str]]
    """
    idtime, fdtime = dates[0], dates[-1]
    idstr, fdstr = idtime.strftime('%Y-%m-%d'), fdtime.strftime('%Y-%m-%d')

    query = {
        'orderby': 'epoch asc',
        f"{'publish_' if endpoint == 'tle_publish' else ''}epoch": f'{idstr}--{fdstr}',
        'format': 'tle',
        'iter_lines': True,
    }

    tles = getattr(st, endpoint)(**query)

    with open(save_path, 'w') as f:
        f.writelines('\n'.join(tles))

    return tles


async def _request(
    dt_start: datetime.date,
    dt_end: datetime.date,
    st: SpaceTrackClient,
    save_dir: str = None,
    endpoint: str = 'tle',
    skip_existing: bool = False,
):
    idstr, fdstr = dt_start.strftime('%Y-%m-%d'), dt_end.strftime('%Y-%m-%d')
    save_path = os.path.join(save_dir, f'{idstr} {fdstr}.txt')

    dates = get_tle_file_list_as_dates(save_dir)
    files = get_tle_file_list(save_dir)
    for f, (d1, d2) in zip(files, dates):
        if d1 <= dt_start and d2 >= dt_end and skip_existing:
            print(
                f'TLEs from {dt_start} -- {dt_end} already covered by {repr(f)}, skipping...'
            )
            return

    success = False
    while not success:
        try:
            await rate_limiter.wait()  # Wait for a slot to be available.
            print(f'Querying TLEs for {dt_start} -- {dt_end}...')
            _query_tles_between(
                st, [dt_start, dt_end], save_path=save_path, endpoint=endpoint
            )
            print('Done! Waiting due to the rate limit...')
            success = True
        except httpx.ConnectError:
            assert not _internet()
            while not _internet():
                print('No internet! waiting for connection...')
                time.sleep(10)
        except httpx.ReadTimeout:
            print('Read timeout... retrying this query')


async def _save_tles(dates: list[tuple[datetime.date, datetime.date]], **kwargs):
    st = _get_spacetrack_client()

    coros = []
    for s, e in dates:
        assert (
            e > s
        ), 'Starting datetimes (dates[i][0]) must be before ending datetimes (dates[i][1])'
        coros.append(_request(s, e, st, **kwargs))
    await asyncio.gather(*coros)


def save_tles(
    dates: list[tuple[datetime.date, datetime.date]],
    save_dir: str = None,
    endpoint: str = 'tle',
    skip_existing: bool = True,
):
    """Queries and saves TLEs for a set of pairs of datetimes

    :param dates: Dates to query pairs for
    :type dates: list[tuple[datetime.date, datetime.date]]
    :param save_dir: Directory to save .txts of TLEs to, defaults to None (the default internal package destination ./txt/*.txt)
    :type save_dir: bool, optional
    :param endpoint: The Space-Track endpoint to query, defaults to 'tle'
    :type endpoint: str, optional
    :param skip_existing: Whether to skip pairs of dates where the TLE file has already been saved, defaults to True
    :type skip_existing: bool, optional
    :type dates: list[datetime.date]
    """
    save_dir = os.environ['TL3_TXT_DIR'] if save_dir is None else save_dir
    kwargs = dict(
        skip_existing=skip_existing,
        save_dir=save_dir,
        endpoint=endpoint,
    )
    asyncio.run(_save_tles(dates, **kwargs))


def _load_secrets():
    if os.path.exists(os.environ['TL3_SECRETS_CACHE']):
        load_dotenv(os.environ['TL3_SECRETS_CACHE'])
    else:
        username = input('Space-Track username: ')
        password = input('Space-Track password: ')

        success = False

        while not success:
            try:
                st = _get_spacetrack_client(username, password)
                st.tle_latest(norad_cat_id=25544, ordinal=1, format='tle')
                success = True
            except (httpx.HTTPStatusError, AuthenticationError) as e:
                print(str(e))
                print(
                    'Incorrect username and/or password for https://www.space-track.org/auth/login, please try again'
                )

        with open(os.environ['TL3_SECRETS_CACHE'], 'w') as f:
            f.write(f'SPACETRACK_USERNAME={username}\n')
            f.write(f'SPACETRACK_PASSWORD={password}\n')

        print(f"Space-Track credentials cached at {os.environ['TL3_SECRETS_CACHE']}")


def delete_credentials_cache():
    """Deletes the local Space-Track credentials cache. Use only if you want to re-input the username and password for whatever reason."""
    if (
        input(
            f"Are you sure you want to remove {os.environ['TL3_SECRETS_CACHE']}? (y/n)"
        ).lower()
        == 'y'
    ):
        os.remove(os.environ['TL3_SECRETS_CACHE'])


def load_query_dates() -> list[tuple[datetime.date, datetime.date]]:
    """Loads the historical TLE query dates. Note that these are distributed such that each resulting .txt file is about 20 MB (~150k TLEs)

    :return: Pairs of query datetimes, increasing in the list and increasing within the tuple entries
    :rtype: list[tuple[datetime.date, datetime.date]]
    """
    with open(
        os.path.join(os.environ['TL3_DIR'], 'resources', 'query_dates.txt'), 'r'
    ) as f:
        dates = [
            datetime.datetime.strptime(x, '%Y-%m-%d').date()
            for x in f.read().splitlines()
        ]

    date_pairs = list(pairwise(dates))
    return date_pairs


def get_tle_file_list(tle_dir: str = None) -> list[str]:
    """Returns a list of the .txt files in a directory

    :param tle_dir: Directory to search for TLEs, defaults to None (uses the default internal location ./txt/)
    :type tle_dir: str, optional
    :return: List of absolute file paths, sorted by increasing date
    :rtype: list[str]
    """
    tle_dir = os.environ['TL3_TXT_DIR'] if tle_dir is None else tle_dir
    files = [
        x
        for x in os.listdir(tle_dir)
        if os.path.getsize(os.path.join(tle_dir, x)) and x.endswith('.txt')
    ]

    files = sorted(
        files, key=lambda x: datetime.datetime.strptime(x.split(' ')[0], '%Y-%m-%d')
    )

    full_paths = [os.path.join(tle_dir, f) for f in files]

    return full_paths


def get_tle_file_list_as_dates(
    tle_dir: str = None,
) -> list[tuple[datetime.date, datetime.date]]:
    """Lists the contents of the TLE directory as a list of tuples of date limits for each file

    :param tle_dir: Directory to search for TLEs, defaults to None (uses the default internal location ./txt/)
    :type tle_dir: str, optional
    :return: List of beginning and ending date tuples for each file, sorted by increasing date
    :rtype: list[tuple[datetime.date, datetime.date]]
    """
    tle_dir = os.environ['TL3_TXT_DIR'] if tle_dir is None else tle_dir

    files = get_tle_file_list(tle_dir)
    dates = []
    for file in files:
        d1, d2 = os.path.split(file)[1].replace('.txt', '').split(' ')
        d1 = datetime.datetime.strptime(d1, '%Y-%m-%d').date()
        d2 = datetime.datetime.strptime(d2, '%Y-%m-%d').date()
        dates.append((d1, d2))
    return dates


def update_tle_cache(tle_dir: str = None) -> None:
    """Updates the cache with any new TLEs up to the beginning of the last UTC day

    :param tle_dir: Directory to search for TLE .txt files, defaults to None (defaults to the internal destination ./txt/)
    :type tle_dir: str, optional
    """
    tle_dir = os.environ['TL3_TXT_DIR'] if tle_dir is None else tle_dir

    today = datetime.datetime.utcnow().date()

    files = get_tle_file_list()

    dates = []
    day_query = datetime.datetime.strptime(
        os.path.split(files[-1])[1].split(' ')[1][:-4], '%Y-%m-%d'
    ).date()

    while True:
        if day_query < today:
            dates.append(day_query)
        elif day_query == today and len(dates):
            dates.append(day_query)
        else:
            break
        day_query += datetime.timedelta(days=1)

    if len(dates):
        date_pairs = list(pairwise(dates))
        save_tles(date_pairs, save_dir=tle_dir)
        print('TLE cache is up to date!')
    else:
        print('TLE cache is up to date!')


def _date_pairs_between(
    date_start: datetime.date, date_end: datetime.date
) -> list[tuple[datetime.date, datetime.date]]:
    dates = []
    d = date_start
    assert date_start < date_end
    while d <= date_end:
        dates.append(d)
        d += datetime.timedelta(days=1)
    return list(pairwise(dates))


def _get_tle_gaps(tle_dir: str) -> list[tuple[datetime.date, datetime.date]]:
    files = get_tle_file_list_as_dates(tle_dir)
    date_gaps = []
    for f1, f2 in pairwise(files):
        if f1[1] != f2[0]:
            date_gaps.extend(_date_pairs_between(f1[1], f2[0]))
    return date_gaps


def fill_tle_gaps(tle_dir: str = None, **kwargs) -> None:
    """Looks for and fills individual days without TLEs in the text cache

    :param tle_dir: Directory to search, defaults to None (if None, uses the default internal location ./txt/)
    :type tle_dir: str, optional
    """
    tle_dir = os.environ['TL3_TXT_DIR'] if tle_dir is None else tle_dir
    dates = _get_tle_gaps(tle_dir)
    save_tles(dates, save_dir=tle_dir, **kwargs)


def _save_file_from_url(url: str, directory: str, save_name: str = None):
    print(f'Saving {url} to {directory}...')

    if save_name is None:
        file_path = os.path.join(directory, url.split('/')[-1])
    else:
        file_path = os.path.join(directory, save_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Create an SSL context that does not verify certificates
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # Pretend to be Safari on Mac
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'
    }

    # Open the URL with custom headers
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=context) as response, open(
        file_path, 'wb'
    ) as out_file:
        # Get total file size
        file_size = int(response.getheader('Content-Length', 0))
        print(f'Found a file with size {file_size}')

        while True:
            buffer = response.read(1024)
            if not buffer:
                break
            out_file.write(buffer)

    if file_path.endswith('.gz'):
        with gzip.open(file_path, 'rb') as f:
            file_content = f.read()
        with open(file_path, 'wb') as f:
            f.write(file_content)
        shutil.move(file_path, file_path[:-3])
