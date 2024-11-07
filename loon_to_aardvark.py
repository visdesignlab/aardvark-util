'''
Converts a single Loon experiment to an Aardvark experiment.
'''
import os
import json
# from google.protobuf import descriptor_pb2
# import google.protobuf.text_format as text_format
import protoDefs.PbCurveList_pb2 as pbCurveList
import protoDefs.RLE_pb2 as rle
import pandas as pd
import numpy as np
from PIL import Image
import tifffile as tf
from imantics import Mask
from geojson import Feature, Polygon, dumps
import util_common as util



IN_FOLDER = './in/'
OUT_FOLDER_ROOT = './out/'
EXPERIMENT_NAME = 'MCF7DrugResponsePanelA_cellgrowthutiltes'
LOON_FOLDER = '.vizMetaData/'

def main():
    OUT_FOLDER = os.path.join(OUT_FOLDER_ROOT, EXPERIMENT_NAME)
    os.makedirs(OUT_FOLDER, exist_ok=True)

    # Load the protobuf metadata file
    mass_over_time_filename = os.path.join(IN_FOLDER, EXPERIMENT_NAME, LOON_FOLDER, 'massOverTime.pb')

    column_dictionary = {} # will be used to map column names to their respective column values

    util.msg_header('Converting Tabular Data', False)
    curve_list = pbCurveList.PbCurveList()
    with open(mass_over_time_filename, 'rb') as f:
        curve_list.ParseFromString(f.read())
        # initialize the columns
        column_dictionary['track_id'] = []

        cell_attr_index_to_name = {}
        for i, cell_level_attr in enumerate(curve_list.pointAttrNames):
            column_dictionary[cell_level_attr] = []
            cell_attr_index_to_name[i] = cell_level_attr

        track_attr_index_to_name = {}
        for i, track_level_attr in enumerate(curve_list.curveAttrNames):
            column_dictionary[track_level_attr] = []
            track_attr_index_to_name[i] = track_level_attr
    
        for curve in curve_list.curveList:
            for point in curve.pointList:
                column_dictionary['track_id'].append(curve.id)
                for i, attr in enumerate(curve.valueList):
                    column_dictionary[track_attr_index_to_name[i]].append(attr)
                for i, attr in enumerate(point.valueList):
                    column_dictionary[cell_attr_index_to_name[i]].append(attr)

    df = pd.DataFrame(column_dictionary)

    # rename column names to match expected aardvark names
    df.rename(columns={
        'Location ID': 'location',
        'condition_drugID': 'Drug',
        'condition_concentration': 'Concentration (um)',
        'X': 'X_original',
        'Y': 'Y_original'
    }, inplace=True)

    # create shifted columns for X and Y
    df['x'] = (df['X_original'] + df['xShift']) / 4.0
    df['y'] = (df['Y_original'] + df['yShift']) / 4.0

    # print(df.head())

    # Save the full dataframe to a parquet file
    df.to_parquet(os.path.join(OUT_FOLDER, 'composite_tabular_data_file.parquet'))

    # group by the "location" and save each grouped dataframe to a csv file
    for name, group in df.groupby('location'):
        location_id = str(int(name))
        # create a folder for each location id
        location_folder = os.path.join(OUT_FOLDER, "loc_" + location_id)
        os.makedirs(location_folder, exist_ok=True)
        group.to_csv(os.path.join(location_folder, 'metadata.csv'), index=False)

    # get list of unique location IDs for convenience
    location_ids = df['location'].unique()
    location_ids = [str(int(x)) for x in sorted(location_ids)]

    # get frame count
    frame_count = df['Frame ID'].max()

    # convert images
    util.msg_header('Converting Images', False)

    image_metadata_filename = os.path.join(IN_FOLDER, EXPERIMENT_NAME, LOON_FOLDER, 'imageMetaData.json')
    image_metadata = json.load(open(image_metadata_filename))
    tile_width = image_metadata['tileWidth']
    tile_height = image_metadata['tileHeight']
    number_of_columns = image_metadata['numberOfColumns']

    for location in location_ids:
        util.msg('Location: ' + location + ' / ' + str(len(location_ids)), False, True)

        # TODO: This would have to be updated if the Loon data has more than one chunk per location.
        image_filename = os.path.join(IN_FOLDER, EXPERIMENT_NAME, 'data' + location, 'D0.jpg')
        # load image into np array
        image = Image.open(image_filename)
        image_np = np.array(image)
        # print(image_np.shape)
        number_of_rows = image_np.shape[0] // tile_height

        # convert to ome tiff file
        frame = 1
        tiff_filename = os.path.join(OUT_FOLDER, 'loc_' + location, 'image_stack.tif')
        with tf.TiffWriter(tiff_filename) as tif:
            for i in range(number_of_rows):
                for j in range(number_of_columns):
                    tile = image_np[i*tile_height:(i+1)*tile_height, j*tile_width:(j+1)*tile_width, 0]
                    tif.write(tile)
                    frame += 1
                    if frame > frame_count:
                        break
    util.msg('Images converted.', False)


    # convert segmentations
    util.msg_header('Converting Segmentations', False)
    for location in location_ids:
        util.msg('Location: ' + location + ' / ' + str(len(location_ids)), False, True)
        segmentation_folder = os.path.join(OUT_FOLDER, 'loc_' + location, 'segmentations')
        os.makedirs(segmentation_folder, exist_ok=True)
        cell_segmentations_folder = os.path.join(OUT_FOLDER, 'loc_' + location, 'segmentations', 'cells')
        os.makedirs(cell_segmentations_folder, exist_ok=True)
        rle_filename = os.path.join(IN_FOLDER, EXPERIMENT_NAME, 'data' + location, 'L0.pb')
        imageLabels = rle.ImageLabels()

        # build lookup dictionary from frame and segment id to cell id
        cell_id_dict = {}
        location_df = df[df['location'] == int(location)]
        for index, row in location_df.iterrows():
            key = str(int(row['Frame ID'])) + '-' + str(int(row['segmentLabel']))
            cell_id_dict[key] = int(row['track_id'])

        with open(rle_filename, 'rb') as f:
            imageLabels.ParseFromString(f.read())
            frame_number = 0
            for i, row in enumerate(imageLabels.rowList):
                j = i % tile_height
                if j == 0:
                    # reset mask
                    mask = np.zeros((tile_height, tile_width), dtype=np.uint32)
                    segment_labels = set()
                    frame_number += 1
                for run in row.row:
                    mask[j, run.start:run.start+run.length] = run.label
                    segment_labels.add(run.label)
                if j == tile_height - 1:
                    for segment_label in segment_labels:
                        segment_mask = mask == segment_label
                        segment_mask = Mask(segment_mask)
                        polygons = segment_mask.polygons()
                        bbox = segment_mask.bbox()
                        bbox_values = [bbox.min_point[0], bbox.max_point[1], bbox.max_point[0], bbox.min_point[1]]
                        key = str(int(frame_number)) + '-' + str(int(segment_label))
                        cell_id = cell_id_dict.get(key, -404) # TODO: make dict

                        for polygon_verts in polygons.points:
                            outer_polygon_coords = polygon_verts.tolist()
                            outer_polygon_coords.append(outer_polygon_coords[0]) # add beginning to end to close loop
                            feature = Feature(geometry=Polygon([outer_polygon_coords]), properties={"id": cell_id,'frame': frame_number}, bbox=bbox_values)
                            util.export_file(dumps(feature), cell_segmentations_folder, '{}-{}'.format(str(frame_number), cell_id), True)
    util.msg('Segmentations converted.', False)

    # convert experiment metadata
    experiment_metadata_filename = os.path.join(IN_FOLDER, EXPERIMENT_NAME, LOON_FOLDER, 'experimentMetaData.json')
    experiment_metadata = json.load(open(experiment_metadata_filename))
    location_tags = {}
    for condition, value in experiment_metadata["locationMaps"].items():
        for value, location_runs in value.items():
            for (start, stop) in location_runs:
                for location in range(int(start), int(stop) + 1):
                    key = str(int(location))
                    if key not in location_tags:
                        location_tags[key] = {}
                    location_tags[key][condition] = value

    aardvark_metadata = {}
    aardvark_metadata['name'] = experiment_metadata['uniqueId']
    aardvark_metadata['headers'] = list(df.columns)
    aardvark_metadata['headerTransforms'] = {
        "time": "Time (h)",
        "frame": "Frame ID",
        "id": "track_id",
        "parent": "track_id",
        "mass": "Mass (pg)",
    }
    aardvark_metadata['compositeTabularDataFile'] = os.path.join(EXPERIMENT_NAME, 'composite_tabular_data_file.parquet')
    location_metadata_list = []
    for location in location_ids:
        location_metadata = {
            "id": location,
            "tabularDataFilename": os.path.join(EXPERIMENT_NAME, 'loc_' + location, 'metadata.csv'),
            "imageDataFilename": os.path.join(EXPERIMENT_NAME, 'loc_' + location, 'images', 'images.companion.ome'),
            "segmentationsFolder": os.path.join(EXPERIMENT_NAME, 'loc_' + location, 'segmentations'),
            "tags": location_tags[location]
        }
        location_metadata_list.append(location_metadata)
    aardvark_metadata['locationMetadataList'] = location_metadata_list

    # Save the Aardvark metadata to a json file
    json.dump(aardvark_metadata, open(os.path.join(OUT_FOLDER_ROOT, f'{EXPERIMENT_NAME}.json'), 'w'))

    return


if __name__ == '__main__':
    main()