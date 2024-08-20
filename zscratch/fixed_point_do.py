import math


def fp_bits_for_places(n, base=10) -> int:
    print(math.log2(base**n))
    return int(math.log2(base**n) + 1)


s = ''

for _i in range(4301):
    s += '9'
    n8 = int(fp_bits_for_places(len(s)) / 8 + 1)
    s_bytes = int(s).to_bytes(length=n8)
    # print(len(s) / s_bytes.__len__())
