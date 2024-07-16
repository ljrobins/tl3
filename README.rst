TL3
...

``tl3`` provides two things: the ability to automatically and efficiently download every two-line element (TLE) ever published by Space-Track (while staying within the API-imposed rate limit), and piping the 28 GB of resulting .txt files into a parquet file for efficient analysis using packages like ``duckdb`` or ``polars``.

Installation
............

``pip install tl3``

The package should work wherever Polars and DuckDB (its primary dependencies) work.

Quickstart
..........

To pull all TLEs from 1958 to the end of the previous UTC day, run:

.. code-block:: python

   import tl3

   date_pairs = tl3.load_query_dates() 
   # Loads nicely-distributed dates to make each api query roughly the same size (20 MB)
   tl3.save_tles(date_pairs) 
   # Makes queries to the Space-Track API, this takes about 5 hours for all dates
   tl3.update_tle_cache() 
   # Pulls any dates after the above query dates were generated
   tl3.build_parquet(from_scratch=True) 
   # Concatenates all TLE txt files into one parquet for efficient querying

This will download (while remaining within the rate limits) ~28 GB of raw TLE ``.txt`` files, and build a single parquet file out of the results. 

Be considerate to Space-Track when using this package. ``tl3`` automatically stays below the rate limit imposed by Space-Track, but do not repeatedly query all TLEs multiple times. The developer of ``tl3`` is not responsible for any consequences resulting from its use.

The first time you import ``tl3``, you will be prompted for your Space-Track login credentials, which are cached locally for all requests.

Querying The Database
.....................

Once the parquet file is built, you can run queries against the full dataset using ``duckdb``. For example, you can query the NORAD catalog IDs for all polar satellites in LEO with at least one TLE produced in 2024 with:

.. code-block:: python

   import tl3
   import duckdb

   df = duckdb.sql(f"""
      SELECT DISTINCT NORAD_CAT_ID FROM {repr(tl3.DB_PATH)}
      WHERE EPOCH BETWEEN '2024-01-01' AND '2025-01-01'
      AND ABS(INC - 90) < 0.1
      AND N < 10
   """).pl()

Which returns a Polars dataframe:

::

   ┌──────────────┐
   │ NORAD_CAT_ID │
   │ ---          │
   │ u32          │
   ╞══════════════╡
   │ 2876         │
   │ 54153        │
   │ 54154        │
   │ 2877         │
   │ 2861         │
   └──────────────┘
