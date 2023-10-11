from math import nan
import numpy as np
import pandas as pd
import tifffile as tf
from imantics import Mask
from geojson import Feature, Polygon
import util_common as util

IN_FOLDER = './in/'
OUT_FOLDER = './out/'


def main():
    matlab_to_csv('jz_march.mat')
    matlab_to_tiff('images/Loc_4_well_23_data1.mat')
    return

def matlab_to_csv(filename: str):
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

def matlab_to_tiff(filename: str):
    matlab_data = util.openAnyMatlabFile(IN_FOLDER + filename)
    image_data = util.getNormalizedMatlabObjectFromKey(matlab_data, 'D_stored')
    with tf.TiffWriter(OUT_FOLDER + 'temp.tif') as tif:
         for frame in range(image_data.shape[2]):
            tif.write(image_data[:, :, frame])

    seg_data = util.getNormalizedMatlabObjectFromKey(matlab_data, 'L_stored')

    frame_number = 0
    for frame in range(image_data.shape[2]):
        frame_number += 1
        seg_frame = seg_data[:,:,frame]
        unique_ids = set(seg_frame.flatten().tolist())
        unique_ids.remove(0)
        feature_list = []
        for seg_id in unique_ids:
            single_seg = seg_frame == seg_id
            mask = Mask(single_seg)
            polygons = mask.polygons()
            bbox = mask.bbox()
            for polygon_verts in polygons.points:
                outer_polygon_coords = polygon_verts.tolist()
                outer_polygon_coords.append(outer_polygon_coords[0]) # add beginning to end to close loop
                feature = Feature(geometry=Polygon([outer_polygon_coords]), properties={"ID": seg_id}, bbox=bbox.MIN_MAX)
                feature_list.append(feature)
            # todo bbox, id, end/start
        util.export_file(feature_list, 'images/', frame_number)
        # print(len(polygons.points))
    return

if __name__ == '__main__':
    main()