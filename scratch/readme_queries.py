import tl3
import duckdb
import datetime

tles = tl3.tles_between(datetime.datetime(2024, 1, 1), datetime.datetime(2024, 1, 2), norad_cat_id='all', return_as='tle')

print(tles)

end

df = duckdb.sql(f"""
    SELECT DISTINCT NORAD_CAT_ID FROM {repr(tl3.DB_PATH)}
    WHERE EPOCH BETWEEN '2024-01-01' AND '2025-01-01'
    AND ABS(INC - 90) < 0.1
    AND N < 10
""").pl()

print(df)

df = duckdb.sql(f"""
    SELECT EPOCH, INC, ECC FROM {repr(tl3.DB_PATH)}
    WHERE NORAD_CAT_ID == 25544
""").pl()

print(df)


