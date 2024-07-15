TL3
...

``tl3`` provides two things: the ability to automatically and efficiently download every two-line element (TLE) ever published by Space-Track (while staying within the API-imposed rate limit), and piping the 28 GB of resulting .txt files into a parquet file for efficient analysis using packages like ``duckdb`` or ``polars``.

Installation
............

``pip install tl3``

Use
...

Once installed, 