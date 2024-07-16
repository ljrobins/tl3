Why ``tl3``?
............

``tl3`` provides two things: the ability to automatically and efficiently download every two-line element (TLE) ever published by Space-Track (while staying within the API-imposed rate limit), and piping the resulting ``.txt`` files into a parquet file for efficient analysis using packages like ``duckdb`` or ``polars``.

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

Once the parquet file is built, you can query TLEs between two dates for a single NORAD ID or the full catalog:

.. code-block:: python

    tles = tl3.tles_between(datetime.datetime(2024, 1, 1), datetime.datetime(2024, 1, 2), norad_cat_id='all', return_as='tle')

::

    [['1 44928U 20001Q   24000.00001156 -.00049610  00000-0 -48650-3 0  9997'
    '2 44928 053.0540 322.4610 0001433 089.1120 141.4850 15.65344620   574']
    ['1 45705U 20035BA  24000.00001156  .00214062  00000-0  83880-3 0  9991'
    '2 45705 053.0460 027.5330 0008402 050.5410 020.3000 15.85815525   605']
    ['1 46031U 20055E   24000.00001156 -.00024118  00000-0 -16770-2 0  9998'
    '2 46031 053.0530 116.6100 0001254 079.9010 008.0290 15.04774666   583']
    ...
    ['1 20962U 75100F   24000.99892966  .00000079  00000-0  00000-0 0  9996'
    '2 20962 004.5720 273.5430 0280693 054.9400 307.9080 01.01930308 12691']
    ['1 20962U 75100F   24000.99892968  .00000079  00000-0  00000-0 0  9996'
    '2 20962 004.5720 273.5430 0280682 054.9380 307.9090 01.01930308 12692']
    ['1 20962U 75100F   24000.99892985  .00000079  00000-0  00000-0 0  9996'
    '2 20962 004.5720 273.5430 0280690 054.9390 307.9080 01.01930308 12694']]


You can also run queries directly against the full dataset using ``duckdb``. For example, you can query the NORAD catalog IDs for all polar satellites in LEO with at least one TLE produced in 2024 with:

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

Or we could get the inclination and eccentricity history of the ISS:

.. code-block:: python

    df = duckdb.sql(f"""
        SELECT EPOCH, INC, ECC FROM {repr(tl3.DB_PATH)}
        WHERE NORAD_CAT_ID == 25544
    """).pl()

::

    shape: (48_981, 3)
    ┌─────────────────────────┬───────────┬──────────┐
    │ EPOCH                   ┆ INC       ┆ ECC      │
    │ ---                     ┆ ---       ┆ ---      │
    │ datetime[μs]            ┆ f32       ┆ f32      │
    ╞═════════════════════════╪═══════════╪══════════╡
    │ 1998-11-21 06:49:59.999 ┆ 51.59     ┆ 0.012536 │
    │ 1998-11-21 07:58:35.072 ┆ 51.617001 ┆ 0.012341 │
    │ 1998-11-21 10:57:42.787 ┆ 51.591    ┆ 0.012586 │
    │ 1998-11-21 12:27:32.846 ┆ 51.595001 ┆ 0.012386 │
    │ 1998-11-21 13:57:13.741 ┆ 51.595001 ┆ 0.012396 │
    │ …                       ┆ …         ┆ …        │
    │ 2024-07-16 10:39:50.426 ┆ 51.637001 ┆ 0.00103  │
    │ 2024-07-16 11:17:07.495 ┆ 51.638    ┆ 0.00102  │
    │ 2024-07-16 17:37:27.269 ┆ 51.638    ┆ 0.001024 │
    │ 2024-07-16 19:56:56.165 ┆ 51.636002 ┆ 0.001031 │
    │ 2024-07-16 20:17:12.377 ┆ 51.638    ┆ 0.001063 │
    └─────────────────────────┴───────────┴──────────┘
