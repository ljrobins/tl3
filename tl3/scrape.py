import ssl
import os
import shutil
import gzip


def save_file_from_url(url: str, directory: str, save_name: str = None):
    import urllib.request

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
