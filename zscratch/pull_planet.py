import datetime
import time
import urllib

import tl3 as tm

save_dir = 'data_pl'
url = (
    lambda date: f'https://ephemerides.planet-labs.com/planet_mc_{date.strftime("%Y%m%d")}.tle'
)

for days_back in range(3000):
    date = datetime.datetime(2023, 4, 21) - datetime.timedelta(days=days_back)

    try:
        tm._save_file_from_url(url(date), save_dir)
    except urllib.error.HTTPError as e:
        if e.status == 403:
            print('Access forbidden, continuing to next day')
            pass
        else:
            raise e
    time.sleep(1)
