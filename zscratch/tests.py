import os

import polars as pl
from hypothesis import given
from hypothesis import strategies as st

import tl3

satcat = pl.read_parquet(os.environ['TL3_SATCAT_PATH'])
all_norad = [int(x) for x in satcat['NORAD_CAT_ID'].to_list()]


@given(norad_id=st.sampled_from(all_norad))
def test_cospar_to_norad(norad_id: int):
    assert tl3.cospar_to_norad(tl3.norad_to_cospar(norad_id)) == norad_id


def test_cospar_to_name():
    # because name is not a unique identifier, we do not hypothesis test this
    assert tl3.cospar_to_name(tl3.name_to_cospar('SPUTNIK 3')) == 'SPUTNIK 3'


def test_name_to_norad():
    # because name is not a unique identifier, we do not hypothesis test this
    assert tl3.norad_to_name(tl3.name_to_norad('SPUTNIK 3')) == 'SPUTNIK 3'


test_cospar_to_norad()
test_cospar_to_name()
test_name_to_norad()
