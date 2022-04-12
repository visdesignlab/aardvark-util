import util_common as util

IN_FOLDER = './in/'
OUT_FOLDER = './out/'


def main():
    filename = 'Loc_1_well_2_CellObjData.mat'
    matlab_data = util.openAnyMatlabFile(IN_FOLDER + filename)
    print(matlab_data)
    return

if __name__ == '__main__':
    main()