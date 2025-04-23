import os
import fnmatch
from matlab_to_all import QUIET_MODE
import util_common as util
from roifile import ImagejRoi
from geojson import Feature, Polygon, FeatureCollection, dumps
from typing import Union, List
import pandas as pd

IN_FOLDER = "./in/"
OUT_FOLDER = "./out/"

QUIET_MODE = False
OVERWRITE = True


REFERENCE_TABLE = "./in/reference_table.csv"
df = pd.read_csv(REFERENCE_TABLE)

# 🧊 ICEBOX 🧊
# - command line args (in, out, quiet, force overwrite)
# - maybe tracks folder, but probably not
# - if remove frames folder, can maybe improve perf of overwrite = False


def main():
    util.msg_header("Finding ROI files", QUIET_MODE)
    pattern = "Track_*.roi"
    filename_list = []
    found_count = 0
    print_every = 10
    for root, _, files in os.walk(IN_FOLDER):
        path = root.replace(IN_FOLDER, "", 1)
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
    filename_list.sort(key=lambda f: (f[0], parse_frame(f[1]), parse_id(f[1])))
    filename_stats = get_filename_stats(filename_list)
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
        frame = parse_frame(name)
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
                os.path.join(OUT_FOLDER, last_path, "frames"),
                str(last_frame),
            )
            feature_list = []
        last_frame = frame
        last_path = path
        filename = os.path.join(IN_FOLDER, path, name)
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
            os.path.join(OUT_FOLDER, last_path, "cells"),
            "{}-{}".format(str(frame), cell_id),
        )
        feature_list.append(feature)

    export(feature_list, os.path.join(OUT_FOLDER, last_path, "frames"), str(last_frame))

    util.return_carriage(QUIET_MODE)
    util.return_carriage(QUIET_MODE)
    util.msg_header("Done 🥂", QUIET_MODE)
    return


def get_filename_stats(filename_list: List) -> dict:
    filename_stats = {}
    for path, name in filename_list:
        frame = parse_frame(name)
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


def parse_frame(filename: str) -> int:
    # get frame from the reference table
    track_id = parse_id(filename)
    if "-" not in filename:
        cell_index = 0
    else:
        cell_index = int(filename.split("-")[1].split(".")[0])
    frames = df.loc[df["LABEL"] == track_id, "FRAME"]
    sorted_frames = sorted(frames.tolist())
    frame = sorted_frames[cell_index]
    return frame


def parse_id(filename: str) -> int:
    if "-" not in filename:
        return filename[:-4]
    return filename.split("-")[0]


if __name__ == "__main__":
    main()
