import os
import glob
import polars as pl


IN_FOLDER = './in/'
OUT_FOLDER = './out/'

def updateParentLookup(lookup, df):
    cellCount = df.n_unique('Tracking ID')
    if (cellCount == 1):
        return
    df = df.groupby('Tracking ID').agg(
    [
        pl.col('Frame').min().alias('Frame.min'),
        pl.col('Frame').max().alias('Frame.max'),
        pl.col('Lineage ID').min() # They should all be the same.
    ])
    maxToId = {}
    ambiguousList = {}
    for (id, _, maxF, _) in df.iter_rows():
        if maxF in maxToId:
            idList = ambiguousList.get(maxF, [])
            idList.append(id)
            ambiguousList[maxF] = idList
        maxToId[maxF] = id

    for (id, minF, _, founder) in df.iter_rows():
        if id == founder:
            continue
        parentsMaxF = minF - 1
        if parentsMaxF in ambiguousList:
            print('WARNING, ambiguous connection: maxF=' + str(parentsMaxF) + ', ' + str(ambiguousList[parentsMaxF]))
        realParent = maxToId[parentsMaxF]
        lookup[id] = realParent
    return

def main(filename):
    df = pl.read_csv(IN_FOLDER + filename, comment_char='#', dtypes={'mCherry - Minimum Intensity ()': pl.Float64}, null_values=['-∞', '∞'])
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
    # print(df)
    df.write_csv(OUT_FOLDER + filename)
    return

if __name__ == '__main__':
    os.chdir(IN_FOLDER)
    csvFiles = glob.glob('*.csv');
    os.chdir('..')
    for filename in csvFiles:
        print('processing ' + filename)
        main(filename)