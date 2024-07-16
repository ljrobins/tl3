import tl3
from itertools import pairwise
import datetime
import os

save_dir = None
parquet_dir = None

files = tl3.get_tle_file_list_as_dates()

dates = tl3.load_query_dates()
# tl3.save_tles(dates[-10:], save_dir=save_dir)
# tl3.fill_tle_gaps()
tl3.update_tle_cache(save_dir)
tl3.build_parquet(save_dir, parquet_dir, from_scratch=True)

