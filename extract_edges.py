import numpy as np
import pandas as pd
import util_common as util

IN_FOLDER = './in/'
OUT_FOLDER = './out/'

def main():
    filename = 'pma_to_pma.csv'
    df = pd.read_csv(IN_FOLDER + filename, usecols=["id", "parent"])
    print(df.describe())
    df = df.drop_duplicates()
    print(df.describe())
    df = df[df['id'] != df['parent']]
    print(df.describe())
    df.to_csv(OUT_FOLDER + 'edges_' + filename, index=False)
    return

if __name__ == '__main__':
    main()