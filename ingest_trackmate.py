# - special steps are required to name the branches of lineages in a way that makes it possible to reconstruct the lineage
# - this exports appends an a/b to the end of the label.
# - they don't export a parent column, but we can fairly easily infer this now. This is what `infer_parent_from_id.py` does.
# - this complicates the link to the roi. (without the special steps the label matches the roi filename exactly) with this, the roi file
#   is in the form {label}-{index}.roi. Where `label` is from the `LABEL` column. Since there are multiple rows with the same label, it includes
#   an index for which one it refers to. This index is zero-indexed, and when index=0 the roi file is simply {label}.roi.
# 👆  🍻🍻🍻 DONE 🍻🍻🍻  👆
# - The TrackMate table also zero-indices the frame column. This needs to be adjusted to one-indexed for things to line up correctly
# - The table should also be sorted by frame before import.
# - `roi_to_geojson_trackmate.py` currently assumes the frame has been sorted and one-indexed (we did this manually for the first import)
#   then will generate the geojson files from the rois correctly.


# - updates with new naming convention
# add a new column for the track ID that strips the spot ID from the label column.
# Actually, simplify the logic for matching the roi files. This looks like it has a 1:1 mapping between label and roi filename.

"""
Convert TrackMate outputs into a format compatable for Loon software.

Inputs: 
- A CSV file from TrackMate
    - Must currently include 'LABEL', 'FRAME', 'POSITION_X', 'POSITION_Y' columns
- A folder containing ROI files from TrackMate

Process:
- Read the CSV file, remove unnecessary rows / columns, sort by frame
- Infer/Add a 'parent' column to the csv file, which includes the parents of each track
- Output that corrected csv
- Convert the that corrected csv to a Parquet file
- Convert ROI files to GeoJSON format, creating a folder structure based on frames

Outputs:
- A metadata.csv file with metadata for Loon
- A metadata.parquet file with metadata for Loon
- A segmentations folder with geojson files for each frame

"""

import os
import argparse
import fnmatch
from matlab_to_all import QUIET_MODE
import util_common as util
from roifile import ImagejRoi
from geojson import Feature, Polygon, FeatureCollection, dumps
from typing import Union, List
import pandas as pd


QUIET_MODE = False
OVERWRITE = True


def main(csv_filename, roi_folder, output_folder):

    # Column names
    frame = "FRAME"
    position_x = "POSITION_X"
    position_y = "POSITION_Y"
    label = "LABEL"
    location = "location"

    # load csv into df
    df = pd.read_csv(csv_filename)

    # delete extra rows with metadata
    df = df.drop([0, 1, 2, 3])
    # df = df.infer_objects() # this made everything an object, but I would've expected this to work

    # reload and clean up temporary file.
    temp_csv = os.path.join(output_folder, "temp.csv")
    df.to_csv(temp_csv, index=False)
    df = pd.read_csv(temp_csv)
    os.remove(temp_csv)  # Clean up the temporary file

    # sort by frame
    # convert frame to int
    df[frame] = df[frame] + 1
    df = df.sort_values(by=[frame])

    # Scaling factor assumes positions rescaled from pixels to microns
    scaling_factor = 1.85
    df[position_x] = df[position_x] * scaling_factor
    df[position_y] = df[position_y] * scaling_factor

    # remove MANUAL_SPOT_COLOR column since it is all empty and is causing problems.
    if "MANUAL_SPOT_COLOR" in df.columns:
        df = df.drop(columns=["MANUAL_SPOT_COLOR"])

    # create new column for the track ID by dropping the spot ID from the label column
    df["loon_track"] = df[label].apply(lambda x: os.path.splitext(x)[0])

    # move new column to first position
    cols = list(df.columns)
    cols.insert(0, cols.pop(cols.index("loon_track")))
    df = df[cols]

    # infer parent from the label.
    output_csv_filename = os.path.join(output_folder, "metadata.csv")
    df = infer_parent_from_id(df, output_csv_filename)

    geojson_output_folder = os.path.join(output_folder, "segmentations")
    roi_to_geojson(df, roi_folder, geojson_output_folder)

    # run bf tools script, either automatically or manually.
    # given an input merged tif with <input_image_path>
    # ./bftools/bfconvert -option ometiff.companion <output_folder>/images/images.companion.ome <input_image_path> <output_folder>/images/image_t%t.ome.tiff
    # e.g. if <input_image_path> is ./in/TRACKMATE_2/Merged.tif and <output_folder> is ./out/TRACKMATE_2
    # then the command would be:
    # ./bftools/bfconvert -option ometiff.companion ./out/TRACKMATE_2/images/images.companion.ome ./in/TRACKMATE_2/Merged.tif ./out/TRACKMATE_2/images/image_t%t.ome.tiff

    # create parquet file from the csv
    df[location] = 2
    df.to_parquet(os.path.join(output_folder, "metadata.parquet"), index=False)

    return

# Given a dataframe with a track label column, create a parent column by infering parent values from labels.
def infer_parent_from_id(df, output_csv):
    # Add a new column 'parent' based on the 'LABEL' column
    def calculate_parent(label):
        if isinstance(label, str):
            if "." not in label:
                return label
            parent = label[:-1].rstrip(".")
            # check if parent exists in the LABEL column
            if parent not in df["loon_track"].values:
                # If parent does not exist, return the original label
                return label
        return parent

    df["parent"] = df["loon_track"].apply(calculate_parent)
    # Reorder columns so 'parent' is the second column
    cols = list(df.columns)
    cols.insert(1, cols.pop(cols.index("parent")))
    df = df[cols]

    util.ensure_directory_exists(output_csv)
    # Save the updated DataFrame to a new CSV file
    df.to_csv(output_csv, index=False)
    return df


######################

# Given a folder of ROI files and a dataframe, outputs a folder of GeoJson files
def roi_to_geojson(df, roi_folder, output_folder):
    # Checks for empty
    util.ensure_directory_exists(output_folder)
    util.msg_header("Finding ROI files", QUIET_MODE)

    # Initialise pattern & filename
    pattern = "Track_*.roi"
    filename_list = []

    
    found_count = 0
    print_every = 10
    for root, _, files in os.walk(roi_folder):
        path = root.replace(roi_folder, "", 1)
        for name in fnmatch.filter(files, pattern):
            filename_list.append((path, name))
            found_count += 1
            if found_count % print_every == 0:
                util.msg(
                    "{} Found: {} files.".format(
                        util.textSpinner(found_count, 10_000), found_count
                    ),
                    QUIET_MODE,
                    True,
                )
    filename_list.sort(key=lambda f: (f[0], parse_frame(f[1], df), parse_id(f[1])))
    filename_stats = get_filename_stats(filename_list, df)
    util.msg(
        "✅ Found: {} files in {} folders.".format(found_count, len(filename_stats)),
        QUIET_MODE,
        True,
    )
    feature_list = []
    last_frame = -1
    last_path = ""
    file_count = 0
    folder_count = 0
    for path, name in filename_list:
        frame = parse_frame(name, df)
        if path != last_path:
            folder_count += 1
            util.return_carriage(QUIET_MODE)
            util.return_carriage(QUIET_MODE)
            util.msg_header(
                "Converting folder [{}/{}]: {}".format(
                    folder_count, len(filename_stats), path
                ),
                QUIET_MODE,
            )
            file_count = 0
        file_count += 1
        util.updateLoadingMessage(
            file_count,
            filename_stats[path]["count"],
            "files. {} of {} frames".format(frame, filename_stats[path]["frames"]),
            False,
        )
        if last_frame != frame and last_frame != -1:
            export(
                feature_list,
                os.path.join(output_folder, last_path, "frames"),
                str(last_frame),
            )
            feature_list = []
        last_frame = frame
        last_path = path
        filename = os.path.join(roi_folder, path, name)
        cell_id = parse_id(name)
        roi = ImagejRoi.fromfile(filename)
        outer_polygon_coords = roi.coordinates().tolist()
        outer_polygon_coords.append(
            outer_polygon_coords[0]
        )  # add beginning to end to close loop
        feature = Feature(
            geometry=Polygon([outer_polygon_coords]),
            properties={"id": cell_id, "frame": frame},
            bbox=[roi.left, roi.bottom, roi.right, roi.top],
        )
        export(
            feature,
            os.path.join(output_folder, last_path, "cells"),
            "{}-{}".format(str(frame), cell_id),
        )
        feature_list.append(feature)

    export(
        feature_list, os.path.join(output_folder, last_path, "frames"), str(last_frame)
    )

    util.return_carriage(QUIET_MODE)
    util.return_carriage(QUIET_MODE)
    util.msg_header("Done 🥂", QUIET_MODE)
    return


def get_filename_stats(filename_list: List, df) -> dict:
    filename_stats = {}
    for path, name in filename_list:
        frame = parse_frame(name, df)
        if path not in filename_stats:
            filename_stats[path] = {"count": 0, "frames": 0}
        filename_stats[path]["count"] += 1
        filename_stats[path]["frames"] = max(filename_stats[path]["frames"], frame)
    return filename_stats


def feature_list_to_json(feature_list: List) -> str:
    feature_collection = FeatureCollection(feature_list)
    return dumps(feature_collection)


def feature_to_json(feature: Feature) -> str:
    return dumps(feature)


def export(data: Union[Feature, List], full_path: str, name: str):
    if isinstance(data, Feature):
        data = feature_to_json(data)
    else:
        data = feature_list_to_json(data)
    util.export_file(data, full_path, name, OVERWRITE)
    return


def parse_frame(filename: str, df) -> int:
    name_base = os.path.splitext(filename)[0]
    frames = df.loc[df["LABEL"] == name_base, "FRAME"]
    if len(frames) == 0 or len(frames) > 1:
        raise ValueError(f"Frame not found for {name_base} in DataFrame.")
    return int(list(frames)[0])


def parse_id(filename: str) -> int:
    name_base = os.path.splitext(filename)[0]
    track_id = os.path.splitext(name_base)[0]
    return track_id


######################
if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Infer parent from LABEL column in a CSV file."
    )
    parser.add_argument("input_csv", help="Path to the input CSV file")
    parser.add_argument("roi_folder", help="Path to the input roi folder")
    parser.add_argument("output_folder", help="Path to the output folder")

    # Parse the arguments
    args = parser.parse_args()

    main(args.input_csv, args.roi_folder, args.output_folder)
