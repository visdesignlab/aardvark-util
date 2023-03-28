from math import nan
import numpy as np
import pandas as pd
import util_common as util

IN_FOLDER = './in/'
OUT_FOLDER = './out/'


def main():
    # filename = 'Loc_1_well_4_CellObjData.mat'
    # filename = 'Loc_4_well_23_cell_obj_struct_newer.mat'
    filename = 'jz_march.mat'
    matlab_data = util.openAnyMatlabFile(IN_FOLDER + filename)
    cell_data_list = util.getNormalizedMatlabObjectFromKey(matlab_data, 'Cells_Struct')[0]
   
    attribute_keys = ['mass', 'MI', 'A', 'ii_stored', 'segID']
    time_key = 'time'
    keys = [time_key]
    keys.extend(attribute_keys)

    id = 'CellID' #'CellNum'
    parent = 'ParentCell'
    data_arrays = []
    edges = []
    noParent = -404
    for cell in cell_data_list:
        cell_id = cell[id][0][0]
        parent_id = cell[parent]
        if len(parent_id) > 0:
            parent_id = parent_id[0][0]
            if cell['FounderMark'][0][0] == 1:
                parent_id = noParent
        else:
            parent_id = noParent
        edges.append([cell_id, parent_id])

        data_length = len(cell[time_key])
        id_col = np.full((data_length, 1), cell[id], dtype='uint')
        parent_col = np.full((data_length, 1), cell[parent], dtype='uint')
        values = [id_col, parent_col]
        for key in keys:
            values.append(cell[key])
        combined = np.array(values).T[0]
        data_arrays.append(combined)

    data_out = np.concatenate(data_arrays, axis=0)
    column_names = ['id', 'parent']
    column_names.extend(keys)
    df = pd.DataFrame(data_out, columns=column_names)
    df['id'] = df['id'].astype(int)
    df['parent'] = df['parent'].astype(int)
    df['parent'] = df['parent'].replace(0, -404)

    df = df.sort_values('time')
    # df.rename(columns={'ii_stored': 'frame'}, inplace=True)
    # df['frame'] = df['frame'].astype(int) - 1
    df.to_csv(OUT_FOLDER + 'data.csv', index=False, header=True)

    # df = pd.DataFrame(edges, columns=['id','parent']).astype(int)
    # df['parent'] = df['parent'].replace(noParent, '')
    # print(df)
    # df.to_csv(OUT_FOLDER + 'edges.csv', index=False, header=True)


    return

if __name__ == '__main__':
    main()