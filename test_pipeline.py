import tl3

dates = tl3.load_query_dates()
tl3.save_tles(dates[-10:], save_dir='data2')
tl3.update_tle_cache('data2')
tl3.build_parquet('data2', 'data2')
