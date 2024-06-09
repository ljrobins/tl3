from bs4 import BeautifulSoup
import urllib.request
import os
import twomillionlines as tm

url = 'https://planet4589.org/space/elements/'
dest_dir = 'data_45'

html_page = urllib.request.urlopen(url)
soup = BeautifulSoup(html_page, "html.parser")
for link in soup.findAll('a'):
    href = link.get('href')
    if '.' not in href:
        url_sub = os.path.join(url, href)
        html_sub_page = urllib.request.urlopen(url_sub)
        soup_sub = BeautifulSoup(html_sub_page, "html.parser")
        for link in soup_sub.findAll('a'):
            href_sub = link.get('href')
            if '?' not in href_sub and '/' not in href_sub:
                full_url = os.path.join(url, href, href_sub)
                dest_file = os.path.join(dest_dir, href_sub)
                if os.path.exists(dest_file):
                    print(f'File {dest_file} already exists, skipping...')
                else:
                    tm.save_file_from_url(full_url, dest_dir)
