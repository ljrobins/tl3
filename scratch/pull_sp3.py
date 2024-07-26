#  odd days?

import datetime
import gzip
import os
import time
import urllib
import urllib.request

from bs4 import BeautifulSoup

import tl3 as tm

gps_epoch = datetime.datetime(1980, 1, 6, 1, 1)
now_wk = 2157
end_gps_wk = 1773

for wk in range(now_wk, end_gps_wk, -1):
    print(wk)
    folder_url = f'http://navigation-office.esa.int/products/gnss-products/{wk}'
    save_path = f'data_gnss/{wk}'

    html_page = urllib.request.urlopen(folder_url)
    soup = BeautifulSoup(html_page, 'html.parser')
    sp3_names = [x.get('href') for x in soup.findAll('a') if 'SP3' in x.get('href')]
    for sp3 in sp3_names:
        sp3_url = os.path.join(folder_url, sp3)
        try:
            tm._save_file_from_url(sp3_url, save_path)
        except gzip.BadGzipFile:
            print(f'{sp3} was a bad gzip file, skipping...')
        time.sleep(1.0)
