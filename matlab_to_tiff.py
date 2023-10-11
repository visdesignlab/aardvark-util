import os
from typing import List
import numpy as np
import tifffile as tf
import util_common as util
from imantics import Polygons, Mask
from geojson import Feature, Polygon, FeatureCollection, dumps

IN_FOLDER = './in/'
OUT_FOLDER = './out/'


def main():

    filename = 'images/Loc_4_well_23_data1.mat'
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
        export_file(feature_list, 'images/', frame_number)

        # print(len(polygons.points))

    return

def export_file(feature_list: List, path: str, frame: int):
    if len(feature_list) == 0:
        return
    feature_collection = FeatureCollection(feature_list)
    json_string = dumps(feature_collection)
    full_path = os.path.join(OUT_FOLDER, path)
    save_path = os.path.join(full_path, str(frame) + '.json')
    if not os.path.exists(full_path):
        os.mkdir(full_path)
    with open(save_path, 'w') as out_file:
        print('saving: ', save_path)
        out_file.write(json_string)
    return   

if __name__ == '__main__':
    main()