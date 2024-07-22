import tl3

# df = duckdb.sql(f"""
#     SELECT DISTINCT NORAD_CAT_ID FROM {repr(tl3.DB_PATH)}
#     WHERE EPOCH BETWEEN '2024-01-01' AND '2025-01-01'
#     AND ABS(INC - 90) < 0.1
#     AND N < 10
# """)

save_dir = None
parquet_dir = None

# files = tl3.get_tle_file_list_as_dates()

# dates = tl3.load_query_dates()
# tl3.save_tles(dates, save_dir=save_dir)
# tl3.fill_tle_gaps()
tl3.update_tle_cache(save_dir)
tl3.build_parquet(save_dir, parquet_dir, from_scratch=False)

