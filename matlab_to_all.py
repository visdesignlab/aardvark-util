from math import nan
from typing import Dict
import numpy as np
import pandas as pd
import tifffile as tf
from imantics import Mask
from geojson import Feature, Polygon
import util_common as util

IN_FOLDER = './in/'
OUT_FOLDER = './out/'
QUIET_MODE = False

def main():
    cell_id_dict = matlab_to_csv('Loc_4_well_23/cells.mat')
    matlab_to_tiff_and_json('Loc_4_well_23/images.mat', cell_id_dict)
    return

def matlab_to_csv(filename: str) -> Dict:
    util.msg_header('Extracting csv from ' + filename, QUIET_MODE)

    matlab_data = util.openAnyMatlabFile(IN_FOLDER + filename)
    cell_data_list = util.getNormalizedMatlabObjectFromKey(matlab_data, 'Cells_Struct')[0]
   
    attribute_keys = ['mass', 'MI', 'A', 'ii_stored', 'x', 'y']
    # segID - number used in mask, need to keep track of for the mask to polygon conversion later
    cell_id_dict = {}
    time_key = 'time'
    keys = [time_key]
    keys.extend(attribute_keys)

    id = 'CellID' #'CellNum'
    parent = 'ParentCell'
    data_arrays = []
    # edges = []
    noParent = -404
    cell_number = 1
    for cell in cell_data_list:
        util.updateLoadingMessage(cell_number, len(cell_data_list), 'cells', QUIET_MODE)
        cell_number += 1
        cell_id = cell[id][0][0]
        for i in range(len(cell['segID'])):
            segID = cell['segID'][i][0]
            frame = cell['ii_stored'][i][0]
            cell_id_dict[str(frame) + '-' + str(segID)] = int(cell_id)
        # parent_id = cell[parent]
        # if len(parent_id) > 0:
        #     parent_id = parent_id[0][0]
        #     if cell['FounderMark'][0][0] == 1:
        #         parent_id = noParent
        # else:
        #     parent_id = noParent
        # edges.append([cell_id, parent_id])

        data_length = len(cell[time_key])
        id_col = np.full((data_length, 1), cell[id], dtype='uint')
        parent_col = np.full((data_length, 1), cell[parent], dtype='uint')
        values = [id_col, parent_col]
        for key in keys:
            values.append(cell[key])
        combined = np.array(values).T[0]
        data_arrays.append(combined)
    util.return_carriage(QUIET_MODE)
    data_out = np.concatenate(data_arrays, axis=0)
    column_names = ['id', 'parent']
    column_names.extend(keys)
    df = pd.DataFrame(data_out, columns=column_names)
    df['id'] = df['id'].astype(int)
    df['parent'] = df['parent'].astype(int)
    df['parent'] = df['parent'].replace(0, -404)

    df = df.sort_values('time')
    df.rename(columns={'ii_stored': 'frame'}, inplace=True)
    # df['frame'] = df['frame'].astype(int) - 1
    out_path = OUT_FOLDER + filename
    out_path = out_path.removesuffix('.mat') + '.csv'
    util.ensure_directory_exists(out_path)
    util.msg('saving...', QUIET_MODE, True)
    df.to_csv(out_path, index=False, header=True)
    util.msg('saving... done.', QUIET_MODE)

    # df = pd.DataFrame(edges, columns=['id','parent']).astype(int)
    # df['parent'] = df['parent'].replace(noParent, '')
    # print(df)
    # df.to_csv(OUT_FOLDER + 'edges.csv', index=False, header=True)
    return cell_id_dict

def matlab_to_tiff_and_json(filename: str, cell_id_dict: Dict):
    util.msg_header('Extracting images from ' + filename, QUIET_MODE)
    matlab_data = util.openAnyMatlabFile(IN_FOLDER + filename)
    image_data = util.getNormalizedMatlabObjectFromKey(matlab_data, 'D_stored')
    out_path = OUT_FOLDER + filename
    out_path = out_path.removesuffix('.mat') + '.tif'
    util.ensure_directory_exists(out_path)
    with tf.TiffWriter(out_path) as tif:
         for frame in range(image_data.shape[2]):
            util.updateLoadingMessage(frame+1, image_data.shape[2], 'frames', QUIET_MODE)
            tif.write(image_data[:, :, frame])
    util.return_carriage(QUIET_MODE)

    util.msg('saving...', QUIET_MODE, True)
    seg_data = util.getNormalizedMatlabObjectFromKey(matlab_data, 'L_stored')
    util.msg('saving... done.', QUIET_MODE)

    util.msg_header('Extracting segmentations from ' + filename, QUIET_MODE)
    for frame_index in range(image_data.shape[2]):
        util.updateLoadingMessage(frame_index+1, image_data.shape[2], 'frames', QUIET_MODE)

        seg_frame = seg_data[:,:,frame_index]
        unique_ids = set(seg_frame.flatten().tolist())
        unique_ids.remove(0)
        feature_list = []
        for seg_id in unique_ids:
            single_seg = seg_frame == seg_id
            mask = Mask(single_seg)
            polygons = mask.polygons()
            bbox = mask.bbox()
            bbox_values = [bbox.min_point[0], bbox.min_point[1], bbox.max_point[0], bbox.max_point[1]]
            key = str(frame_index + 1) + '-' + str(seg_id)
            # print(cell_id_dict)
            # print(key)
            cell_id = cell_id_dict.get(key, -404)
            # print(cell_id)
            for polygon_verts in polygons.points:
                outer_polygon_coords = polygon_verts.tolist()
                outer_polygon_coords.append(outer_polygon_coords[0]) # add beginning to end to close loop
                feature = Feature(geometry=Polygon([outer_polygon_coords]), properties={"ID": cell_id}, bbox=bbox_values)
                feature_list.append(feature)
        out_path = OUT_FOLDER + filename
        out_path = out_path.removesuffix('.mat') + '/'
        util.export_file(feature_list, out_path, frame_index + 1)
    util.return_carriage(QUIET_MODE)
    util.msg('done.', QUIET_MODE)
    return

if __name__ == '__main__':
    main()