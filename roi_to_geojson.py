import os
import fnmatch
from matlab_to_all import QUIET_MODE
import util_common as util
from roifile import ImagejRoi
from geojson import Feature, Polygon

IN_FOLDER = './in/'
OUT_FOLDER = './out/'

QUIET_MODE = False


# TODO:
# - cells folder
# - better progress output (split percent by folders)
# - command line args (in, out, quiet, force overwrite)
# - avoid overwrite by default
# - maybe tracks folder, but probably not

def main():
    util.msg_header('Finding ROI files', QUIET_MODE)
    pattern = '*.roi'
    filename_list = []
    found_count = 0
    print_every = 10
    for root, _, files in os.walk(IN_FOLDER):
        path = root.replace(IN_FOLDER, '', 1)
        for name in fnmatch.filter(files, pattern):
            filename_list.append((path, name))
            found_count += 1
            if found_count % print_every == 0:
                util.msg('{} Found: {} files.'.format(util.textSpinner(found_count, 10_000), found_count), QUIET_MODE, True)
    util.msg('✅ Found: {} files'.format(found_count), QUIET_MODE, True)
    filename_list.sort(key=lambda f: (f[0], parse_frame(f[1]), parse_id(f[1])))
    util.return_carriage(QUIET_MODE)
    feature_list = []
    last_frame = -1
    last_path = ''
    # last_folder = ''
    util.msg_header('Converting ROI to GeoJSON', QUIET_MODE)
    for index, (path, name) in enumerate(filename_list):
        util.updateLoadingMessage(index + 1, len(filename_list), '[{}]'.format(path), False)
        # if last_folder != path:
        #     print()
        #     last_folder = path
        frame = parse_frame(name)
        if last_frame != frame:
            # print(path, 'frame:', frame)
            util.export_file(feature_list, os.path.join(OUT_FOLDER, last_path, 'frames'), last_frame)
            feature_list = []
        last_frame = frame
        last_path = path
        filename = os.path.join(IN_FOLDER, path, name)
        cell_id = parse_id(name)
        roi = ImagejRoi.fromfile(filename)
        outer_polygon_coords = roi.coordinates().tolist()
        outer_polygon_coords.append(outer_polygon_coords[0]) # add beginning to end to close loop
        feature = Feature(geometry=Polygon([outer_polygon_coords]), properties={"id": cell_id, 'frame': frame}, bbox=[roi.left, roi.bottom, roi.right, roi.top])
        feature_list.append(feature)

    util.export_file(feature_list, os.path.join(OUT_FOLDER, last_path, 'frames'), last_frame)
    util.return_carriage(QUIET_MODE)
    util.msg_header('Done 🥂', QUIET_MODE)
    return

def parse_frame(filename: str) -> int:
    return int(filename.split('-')[0])

def parse_id(filename: str) -> int:
    return filename.split('-')[1].split('.')[0]

if __name__ == '__main__':
    main()