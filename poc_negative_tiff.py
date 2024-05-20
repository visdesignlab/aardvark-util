import numpy as np
import imageio

'''
Proof of concept for tiffs with negative values.
'''

# Create a 2D array with positive and negative values
array = np.zeros((100, 100), dtype=np.int16)
# populate the array with values, each column is a single value, from -50 to 50
for i in range(100):
    array[:, i] = i - 50

# print the first row of the array
print('Original Data')
print(array.dtype)
print(array[0, :])

# Save the array as a TIFF file
imageio.imwrite('./out/poc_negative_tiff.tif', array)


# Load the TIFF file
arrayFromTiff = imageio.imread('./out/poc_negative_tiff.tif')

# print the first row of the array
print('data loaded from Tiff')
print(arrayFromTiff.dtype)
print(arrayFromTiff[0, :])