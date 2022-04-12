import math
from typing import Union
import h5py
from scipy.io import loadmat
import numpy as np

def openAnyMatlabFile(matlabFilename: str) -> Union[dict, h5py.File]:
    try:
        outputDict = h5py.File(matlabFilename, 'r')
    except:
        print('using loadmat')
        outputDict = loadmat(matlabFilename)
    return outputDict

def getNormalizedMatlabObjectFromKey(matlabDict: Union[dict, h5py.File], key: str):
    if key not in matlabDict:
        return None
    if type(matlabDict) == dict:
        return matlabDict[key]
        # return np.array(matlabDict[key]).T
    # else it is an h5py file, which has to be transposed
    # (https://www.mathworks.com/matlabcentral/answers/308303-why-does-matlab-transpose-hdf5-data)
    return np.array(matlabDict[key]).T

def err(msg: str) -> None:
    print('🟥──ERROR──🟥:', msg)
    return

def warn(msg: str, quietMode: bool) -> None:
    if not quietMode:
        print('\t🟡──Warning──🟡:', msg)
    return

def info(msg: str, quietMode: bool) -> None:
    if not quietMode:
        print('\tInfo:', msg)
    return

def msg_header(msg: str, quietMode: bool = False) -> None:
    if not quietMode:
        print(msg)
    return

def msg(msg: str, quietMode: bool, sameLine: bool = False) -> None:
    endString = '\n'
    if sameLine:
        endString = '\r'
    if not quietMode:
        print('\t' + msg, end=endString)
    return

LOADING_BAR_CONSTANT = 0.002345 # somewhat arbitrary constant so printing messages aren't overdone. But seem irregular.

def loadingBar(top: int, bot: int, width = 20) -> str:
    singleProgress = '──░░░▒▒▓'
    percent = top / bot
    count = percent * width
    doneCount = math.floor(count)
    leftOver = count - doneCount
    progressBar = '█' * doneCount
    if doneCount < width:
        idx = math.floor(leftOver * len(singleProgress))
        singleChar = singleProgress[idx]
        progressBar += singleChar
        progressBar += '─' * (width - (doneCount + 1))
    return progressBar + ' {:.2f}%, {} of {}'.format(percent * 100, top, bot)