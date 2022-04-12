import numpy as np
import pandas as pd
import util_common as util

IN_FOLDER = './in/'
OUT_FOLDER = './out/'


def main():
    # filename = 'Loc_1_well_4_CellObjData.mat'
    filename = 'test.mat'
    matlab_data = util.openAnyMatlabFile(IN_FOLDER + filename)
    cell_data_list = util.getNormalizedMatlabObjectFromKey(matlab_data, 'Cells_Struct')[0]
   
    attribute_keys = ['mass', 'MI', 'A']
    time_key = 'time'
    keys = [time_key]
    keys.extend(attribute_keys)

    id = 'CellNum'
    parent = 'ParentCell'
    data_arrays = []
    for cell in cell_data_list:
        data_length = len(cell[time_key])
        id_col = np.full((data_length, 1), cell[id])

        values = [id_col]
        for key in keys:
            values.append(cell[key])
        combined = np.array(values).T[0]
        data_arrays.append(combined)

    data_out = np.concatenate(data_arrays, axis=0)
    # print(data_out.shape)

    return

if __name__ == '__main__':
    main()