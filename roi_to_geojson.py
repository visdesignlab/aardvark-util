import os
import fnmatch
from typing import List
from roifile import ImagejRoi
from geojson import Feature, Polygon, FeatureCollection, dumps

IN_FOLDER = './in/'
OUT_FOLDER = './out/'


def main():

    pattern = '*.roi'
    filename_list = []
    for root, _, files in os.walk(IN_FOLDER):
        path = root.replace(IN_FOLDER, '', 1)
        for name in fnmatch.filter(files, pattern):
            filename_list.append((path, name))
    filename_list.sort(key=lambda f: (f[0], parse_frame(f[1]), parse_id(f[1])))

    feature_list = []
    last_frame = -1
    last_path = ''
    for path, name in filename_list:
        frame = parse_frame(name)
        if last_frame != frame:
            export_file(feature_list, last_path, last_frame)
            feature_list = []
        last_frame = frame
        last_path = path
        filename = os.path.join(IN_FOLDER, path, name)
        cell_id = parse_id(name)
        roi = ImagejRoi.fromfile(filename)
        outer_polygon_coords = roi.coordinates().tolist()
        outer_polygon_coords.append(outer_polygon_coords[0]) # add beginning to end to close loop
        feature = Feature(geometry=Polygon([outer_polygon_coords]), properties={"ID": cell_id}, bbox=[roi.left, roi.bottom, roi.right, roi.top])
        feature_list.append(feature)

    export_file(feature_list, last_path, last_frame)
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

def parse_frame(filename: str) -> int:
    return int(filename.split('-')[0])

def parse_id(filename: str) -> int:
    return int(filename.split('-')[1].split('.')[0])

if __name__ == '__main__':
    main()