import datetime
import os

import mirage as mr
import numpy as np
import polars as pl


def make_weekly_data(search_dir: str) -> dict:
    files = [
        os.path.join(search_dir, x)
        for x in os.listdir(search_dir)
        if 'FIN' in x and x.endswith('.SP3')
    ]
    if not len(files):
        files = [
            os.path.join(search_dir, x)
            for x in os.listdir(search_dir)
            if 'RAP' in x and x.endswith('.SP3')
        ]

    week_data = {}
    cur_time = None
    for file in files:
        with open(file, 'r') as f:
            for line in f:
                if line.startswith('*  '):
                    cur_time = datetime.datetime.strptime(
                        line, '*  %Y  %m %d %H %M %S.%f00 '
                    )
                    tx = mr.itrf_to_j2000(cur_time)
                if line.startswith('P'):
                    sat_identifier = line[1:4]
                    pos_itrf = tuple(
                        [float(x) for x in ' '.join(line[5:].split()).split()][:-1]
                    )
                    pos_j2000 = (tx @ np.array(pos_itrf)).tolist()
                    if sat_identifier not in week_data:
                        week_data[sat_identifier] = [[cur_time, *pos_j2000]]
                    else:
                        week_data[sat_identifier].append([cur_time, *pos_j2000])
    return week_data


def make_weekly_df(week_data: dict) -> pl.DataFrame:
    dfs = []
    for k, v in week_data.items():
        dfs.append(
            pl.DataFrame(v)
            .cast({pl.Float64: pl.Float32})
            .rename(
                {
                    'column_0': 'date',
                    'column_1': f'{k}_j2000_x',
                    'column_2': f'{k}_j2000_y',
                    'column_3': f'{k}_j2000_z',
                }
            )
            .unique('date')
            .sort(pl.col('date'))
        )

    overall_df = dfs[0]
    for df in dfs[1:]:
        overall_df = overall_df.join(df, on=pl.col('date'), how='full', coalesce=True)
    return overall_df


if __name__ == '__main__':
    weeks_sorted = sorted(
        [x for x in os.listdir('data_gnss') if x.isdigit()],
        key=lambda x: int(x),
        reverse=True,
    )
    weeks_sorted = [x for x in weeks_sorted if int(x) < 2300]
    for week in weeks_sorted:
        print(week)
        search_dir = os.path.join('data_gnss', week)
        save_path = os.path.join('proc', 'gnss', f'{week}.parquet')

        weekly_data = make_weekly_data(search_dir)
        weekly_df = make_weekly_df(weekly_data)
        weekly_df.write_parquet(save_path)
