from uuid import uuid4
from pathlib import Path
from tifffile import TiffFile
from ome_types import from_xml, to_xml
from ome_types.model import (
    OME, Image, Pixels, Channel, TiffData
)
# from ome_types.model.simple_types import UUID

# Your two OME-TIFFs, each representing one channel of the same scene
files = [
    Path("./input/shukrans_omes/raw_abs_loc_1.ome.tiff"),
    Path("./input/shukrans_omes/raw_ph_loc_1.ome.tiff")
]

filenames = [f.name for f in files]

companion_dir = Path("./output/multitest")


def rel(p):  # relative path from companion file to TIFF
    return str(Path(p).resolve().relative_to(companion_dir.resolve()))

def read_geom(path):
    with TiffFile(path) as t:
        ome = from_xml(t.ome_metadata or "")
        img = ome.images[0]
        px = img.pixels
        # try to reuse source UUID if present
        src_uuid = None
        # if px.tiff_data and px.tiff_data[0].uuid and px.tiff_data[0].uuid.value:
            # src_uuid = px.tiff_data[0].uuid.value
        if not src_uuid:
            src_uuid = f"urn:uuid:{uuid4()}"
        return dict(
            size_x=px.size_x, size_y=px.size_y, size_z=px.size_z,
            size_t=px.size_t, pixel_type=px.type, dim_order=px.dimension_order,
            phys=(px.physical_size_x, px.physical_size_x_unit,
                  px.physical_size_y, px.physical_size_y_unit,
                  px.physical_size_z, px.physical_size_z_unit),
            uuid=src_uuid
        )

g0 = read_geom(files[0])
g1 = read_geom(files[1])
assert (g0["size_x"], g0["size_y"], g0["size_z"], g0["size_t"]) == (g1["size_x"], g1["size_y"], g1["size_z"], g1["size_t"])
assert g0["pixel_type"] == g1["pixel_type"]
assert g0["dim_order"]  == g1["dim_order"]


# ---- Read metadata from the first file to establish shape/type ----
with TiffFile(files[0]) as tif0:
    ome0_xml = tif0.ome_metadata
    if not ome0_xml:
        raise ValueError(f"No OME-XML in {files[0]}")
    ome0 = from_xml(ome0_xml)
    img0 = ome0.images[0]
    px0 = img0.pixels

    size_x = px0.size_x
    size_y = px0.size_y
    size_z = px0.size_z
    size_t = px0.size_t
    pixel_type = px0.type
    dim_order = px0.dimension_order  # e.g. "XYZCT"

# ---- Validate the second file matches core geometry/type ----
with TiffFile(files[1]) as tif1:
    ome1_xml = tif1.ome_metadata
    if not ome1_xml:
        raise ValueError(f"No OME-XML in {files[1]}")
    ome1 = from_xml(ome1_xml)
    img1 = ome1.images[0]
    px1 = img1.pixels

    assert (px1.size_x, px1.size_y, px1.size_z, px1.size_t) == (size_x, size_y, size_z, size_t), \
        "Files must have identical X/Y/Z/T to combine into one Pixels."
    assert px1.type == pixel_type, "Pixel types must match."
    assert px1.dimension_order == dim_order, "Dimension order must match."

# ---- Build a single Pixels with SizeC=2 and Channels ----
channels = [
    Channel(id="Channel:0", name=files[0].name, samples_per_pixel=1),
    Channel(id="Channel:1", name=files[1].name, samples_per_pixel=1),
]

# We point each channel’s planes to its source file via TiffData.
# Use each file's UUID if available; otherwise create a UUID element without a value (still valid),
# but it’s better to reuse the file’s existing UUID when present.
# def extract_uuid_and_plane_count(ome_image, fallback_name):
#     # Try to find a UUID already present in TiffData; otherwise, only set file_name
#     # td_list = ome_image.pixels.tiff_data or []
#     td_list = []
#     uuid_val = fallback_name
#     if td_list and td_list[0].uuid and td_list[0].uuid.value:
#         uuid_val = td_list[0].uuid.value
#     # plane_count should cover all Z*T planes for a single-channel file
#     plane_count = ome_image.pixels.size_z * ome_image.pixels.size_t
#     # return "blargen", plane_count
#     # return UUID(value=uuid_val, file_name=fallback_name), plane_count
#     return {"value": uuid_val, "file_name": fallback_name}, plane_count

def extract_uuid_and_plane_count(ome_img, fallback_name):
    # td = ome_img.pixels.tiff_data or []
    td = []
    # try to reuse existing UUID from the source file
    src_uuid = td[0].uuid.value if (td and td[0].uuid and td[0].uuid.value) else None
    if not src_uuid:
        # generate a stable OME-style URN
        src_uuid = f"urn:uuid:{uuid4()}"
    planes = ome_img.pixels.size_z * ome_img.pixels.size_t
    return {"value": src_uuid, "file_name":fallback_name}, planes

uuid0, planes0 = extract_uuid_and_plane_count(img0, files[0].name)
uuid1, planes1 = extract_uuid_and_plane_count(img1, files[1].name)

print(f"File 0: {files[0]} UUID={uuid0} planes={planes0}")
print(f"File 1: {files[1]} UUID={uuid1} planes={planes1}")


# Each TiffData maps a contiguous block of planes starting at FirstZ/FirstT/FirstC.
# We assign channel 0 and channel 1 respectively, spanning all Z*T planes.
# tiffdata = [
#     TiffData(uuid=uuid0, first_c=0, first_z=0, first_t=0, plane_count=planes0),
#     TiffData(uuid=uuid1, first_c=1, first_z=0, first_t=0, plane_count=planes1),
# ]

tiffdata = []
for c, (file_path, g) in enumerate([(filenames[0], g0), (filenames[1], g1)]):
    print('~~~')
    print(g)
    print(g["uuid"])
    print(Path(file_path).resolve())
    for t in range(size_t):
        tiffdata.append(
            TiffData(
                uuid={"value":g["uuid"], "file_name":file_path},
                first_c=c, first_z=0, first_t=t,
                plane_count=1,
                ifd=t  # most OME-TIFF writers store T along IFDs
            )
        )


pixels = Pixels(
    id="Pixels:0",
    dimension_order=dim_order,  # e.g., "XYZCT"
    size_x=size_x,
    size_y=size_y,
    size_z=size_z,
    size_c=2,        # <- one Image, two channels
    size_t=size_t,
    type=pixel_type, # e.g., "uint16"
    channels=channels,
    tiff_data_blocks=tiffdata
)

image = Image(
    id="Image:0",
    name="Merged-2C",  # whatever name you want for the combined image
    pixels=pixels
)

combined = OME(images=[image])

with open("./output/multitest/companion2.ome.xml", "w") as f:
    f.write(to_xml(combined))

print("Wrote companion2.ome.xml (1 Image, 2 Channels).")
