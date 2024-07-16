#  odd days?

import datetime
import tl3 as tm
import urllib
import time

url = (
    lambda date: f'https://nasa-public-data.s3.amazonaws.com/iss-coords/{date.strftime("%Y-%m-%d")}/ISS_OEM/ISS.OEM_J2K_EPH.txt'
)
save_dir = 'data_iss'

end_date = datetime.datetime(2020, 1, 1)
now = datetime.datetime(2022, 10, 14)

for days_back in range((now - end_date).days):
    date = now - datetime.timedelta(days=days_back)
    df = date.strftime('%Y-%m-%d')
    durl = url(date)
    save_name = f'ISS_OEM_J2K_EPH_{df}.txt'
    try:
        tm._save_file_from_url(durl, save_dir, save_name=save_name)
    except urllib.error.HTTPError:
        print(f'No file for {df}')
    time.sleep(1.0)
