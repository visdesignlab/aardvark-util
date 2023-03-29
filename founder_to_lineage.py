from math import nan
import numpy as np
import util_common as util
import polars as pl


IN_FOLDER = './in/'
OUT_FOLDER = './out/'

def updateParentLookup(lookup, df):
    return

def main():
    filename = 'R3_D10_16_cell104.csv'
    df = pl.read_csv(IN_FOLDER + filename, dtypes={'mCherry - Minimum Intensity ()': pl.Float64}, null_values=['-∞', '∞'])
    # print(df)
    parentLookupDF = df.select(pl.col('Tracking ID'), (pl.col('Lineage ID')).alias('Parent ID')).unique()
    # print(parentLookupDF)
    parentLookup = {}
    for row in parentLookupDF.iter_rows():
        parentLookup[row[0]] = row[1]
    # print(parentLookup)
    grouped = df.groupby('Lineage ID')
    # print(grouped)
    for name, data in grouped:
        updateParentLookup(parentLookup, data)

    parentLookupDF = pl.DataFrame({'Tracking ID': parentLookup.keys(), 'Parent ID': parentLookup.values()})
    df = df.join(parentLookupDF, on='Tracking ID')
    print(df)
    df.write_csv(OUT_FOLDER + filename)
    return

if __name__ == '__main__':
    main()