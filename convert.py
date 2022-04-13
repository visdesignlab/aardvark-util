import numpy as np
import pandas as pd
import util_common as util

IN_FOLDER = './in/'
OUT_FOLDER = './out/'


def main():
    # filename = 'Loc_1_well_4_CellObjData.mat'
    filename = 'struct_5.mat'
    matlab_data = util.openAnyMatlabFile(IN_FOLDER + filename)
    cell_data_list = util.getNormalizedMatlabObjectFromKey(matlab_data, 'Cells_Struct')[0]
   
    attribute_keys = ['mass', 'MI', 'A']
    time_key = 'time'
    keys = [time_key]
    keys.extend(attribute_keys)

    id = 'CellNum'
    parent = 'ParentCell'
    data_arrays = []
    edges = []
    for cell in cell_data_list:
        cell_id = cell[id][0][0]
        parent_id = cell[parent]
        if len(parent_id) > 0:
            parent_id = parent_id[0][0]
        else:
            if cell['Origin'][0][0] != 'f':
                continue
            parent_id = -1
        edges.append([cell_id, parent_id])

        data_length = len(cell[time_key])
        id_col = np.full((data_length, 1), cell[id], dtype='uint')
        values = [id_col]
        for key in keys:
            values.append(cell[key])
        combined = np.array(values).T[0]
        data_arrays.append(combined)



    data_out = np.concatenate(data_arrays, axis=0)
    column_names = ['id']
    column_names.extend(keys)
    df = pd.DataFrame(data_out, columns=column_names)
    df['id'] = df['id'].astype(int)
    df.to_csv(OUT_FOLDER + 'data.csv', index=False, header=True)

    df = pd.DataFrame(edges, columns=['id','parent']).astype(int)
    df['parent'] = df['parent'].replace(-1, '')
    print(df)
    df.to_csv(OUT_FOLDER + 'edges.csv', index=False, header=True)


    return

if __name__ == '__main__':
    main()