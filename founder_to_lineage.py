from math import nan
import numpy as np
import util_common as util
import polars as pl


IN_FOLDER = './in/'
OUT_FOLDER = './out/'


def main():
    filename = 'R3_D10_16_cell104.csv'
    df = pl.read_csv(IN_FOLDER + filename, dtypes={'mCherry - Minimum Intensity ()': pl.Float64}, null_values=['-∞', '∞'])
    print(df)
    df = df.filter(pl.col('Tracking ID') != pl.col('Lineage ID'))
    print(df)
    grouped = df.groupby('Tracking ID').agg(
        [
            pl.col('Frame').min().alias('Frame.min'),
            pl.col('Frame').max().alias('Frame.max'),
            pl.col('Lineage ID').min() # They should all be the same.
        ])
    grouped = grouped.sort('Frame.min')
    
    print(grouped.head(5))
    print(grouped.tail(5))

    # for name, data in grouped:
    #     data.with_columns()
    #     data.row(1)['Frame'] = 66        
    #     print(name)
    #     print(data)
    # df = df[df['Tracking ID'] != df['Lineage ID']]
    # print(df)
    # df_grouped = df.groupby('Tracking ID')
    # df_grouped['Frame'] = 6
    # print(df_grouped)
    return

if __name__ == '__main__':
    main()