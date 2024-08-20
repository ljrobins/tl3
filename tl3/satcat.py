import os

import polars as pl

from .query import _pull_satcat


def load_satcat() -> pl.DataFrame:
    """Loads the satellite catalog dataframe

    :return: The satellite catalog
    :rtype: pl.DataFrame
    """
    if not os.path.exists(os.environ['TL3_SATCAT_PATH']):
        _pull_satcat()
    return pl.read_parquet(os.environ['TL3_SATCAT_PATH'])


def cospar_to_norad(cospar_id: str) -> int:
    df = load_satcat()
    return int(df.filter(pl.col('INTLDES') == cospar_id)['NORAD_CAT_ID'][0])


def norad_to_cospar(norad_id: int) -> str:
    df = load_satcat()
    return df.filter(pl.col('NORAD_CAT_ID') == str(norad_id))['INTLDES'][0]


def name_to_cospar(name: str) -> str:
    df = load_satcat()
    return df.filter(pl.col('SATNAME').str.to_lowercase() == name.lower())['INTLDES'][0]


def cospar_to_name(cospar_id: str) -> str:
    df = load_satcat()
    return df.filter(pl.col('INTLDES') == cospar_id)['SATNAME'][0]


def name_to_norad(name: str) -> int:
    df = load_satcat()
    return int(
        df.filter(pl.col('SATNAME').str.to_lowercase() == name.lower())['NORAD_CAT_ID'][
            0
        ]
    )


def norad_to_name(norad_id: int) -> str:
    df = load_satcat()
    return df.filter(pl.col('NORAD_CAT_ID') == str(norad_id))['SATNAME'][0]
