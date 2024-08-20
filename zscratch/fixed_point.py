def fp_bits_for_places(n, base=10) -> int:
    k = 0
    while base**n - 2**k > 0:
        k += 1
    return k


l1 = '1 25544U 98067A   24213.90256772  .00036721  00000-0  66010-3 0  9999'
l2 = '2 25544 051.6370 093.7860 0005973 147.7960 320.0620 15.49475956 46545'
t1 = len(l1) + len(l2)

print(f'Stored as utf-8: {t1} bytes ({t1*200e6/1e9} GB)')

l1_no_whitespace = '125544U98067A  24213.90256772 .00036721 00000-0 66010-309999'
l2_no_whitespace = (
    '225544 051.6370 093.7860 0005973 147.7960 320.0620 15.49475956 46545'
)
t2 = len(l1_no_whitespace) + len(l2_no_whitespace)

print(f'Whitespace removed utf-8: {t2} bytes ({t2*200e6/1e9} GB)')

l1_just_sgp4 = '2554498067A  24213.90256772'
l2_just_sgp4 = '051.6370093.78600005973147.7960320.062015.49475956'
t3 = len(l1_just_sgp4) + len(l2_just_sgp4)

print(f'Minimal sgp4 utf-8: {t3} bytes ({t3*200e6/1e9} GB)')

l1_better_dtypes = (fp_bits_for_places(3, base=24) + fp_bits_for_places(13 + 10)) / 8
l2_better_dtypes = fp_bits_for_places(len(l2_just_sgp4.replace('.', ''))) / 8
t4 = l1_better_dtypes + l2_better_dtypes

print(f'sgp4 binary: {t4} bytes ({t4*200e6/1e9} GB)')

# assuming we can look up the intl-des from the norad id
l1_keyed_identity = fp_bits_for_places(13 + 5) / 8
l2_better_dtypes = fp_bits_for_places(len(l2_just_sgp4.replace('.', ''))) / 8
t5 = l1_keyed_identity + l2_better_dtypes

print(f'sgp4 binary keyed: {t5} bytes ({t5*200e6/1e9} GB)')

# rounding the date to 6 decimal places instead of 8, and cutting one decimal place off of all l2 floats (6 total)

l1_rounded = fp_bits_for_places(11 + 5) / 8
l2_rounded = fp_bits_for_places(len(l2_just_sgp4.replace('.', '')) - 6) / 8
t6 = l1_rounded + l2_rounded

print(f'sgp4 binary keyed rounded: {t6} bytes ({t6*200e6/1e9} GB)')
