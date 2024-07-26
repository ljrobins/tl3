import os

import polars as pl

import tl3

print(tl3.cospar_to_norad('1998-067A'))
print(tl3.norad_to_cospar(25544))
print(tl3.name_to_cospar('SPUTNIK 3'))
print(tl3.cospar_to_name('1958-004B'))
print(tl3.name_to_norad('SPUTNIK 3'))
print(tl3.norad_to_name(8))
