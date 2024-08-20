import datetime

import numpy as np

import tl3

df_cospar = tl3.tles_between(
    date_start=datetime.datetime(2024, 1, 1),
    date_end=datetime.datetime(2024, 1, 2),
    identifier='2020-035BA',
)
df_norad = tl3.tles_between(
    date_start=datetime.datetime(2024, 1, 1),
    date_end=datetime.datetime(2024, 1, 2),
    identifier=45705,
)

print(np.all(df_cospar.to_numpy() == df_norad.to_numpy()))

# tl3.build_parquet(from_scratch=True)

# pl.Config.set_tbl_rows(100)
# pl.Config.set_tbl_width_chars(1000)
# dfs = pl.DataFrame({"Column": df.schema.keys(), "Type": df.schema.values()})
# print(dfs)

# print(dfs.glimpse())
