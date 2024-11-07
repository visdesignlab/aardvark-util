BFCONVERT=~/Downloads/bftools/bfconvert
PATH_ROOT=./out/MCF7DrugResponsePanelA_cellgrowthutiltes/
LOCATION_COUNT=864
for LOCATION in $(seq 1 $LOCATION_COUNT); do
    $BFCONVERT -option ometiff.companion ${PATH_ROOT}loc_${LOCATION}/images/images.companion.ome ${PATH_ROOT}loc_${LOCATION}/image_stack.tif ${PATH_ROOT}loc_${LOCATION}/images/image_t%t.ome.tiff
done