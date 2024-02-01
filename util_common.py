import math
import os
from typing import Union, List
import h5py
from scipy.io import loadmat
import numpy as np
from geojson import FeatureCollection, dumps

def openAnyMatlabFile(matlabFilename: str) -> Union[dict, h5py.File]:
    try:
        outputDict = h5py.File(matlabFilename, 'r')
    except:
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

def return_carriage(quietMode: bool) -> None:
    # call after sameLine=True if you want it to be preserved (e.g. last frame of loading bar)
    msg_header('', quietMode)

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

def updateLoadingMessage(top: int, bot: int, item: str, quietMode: bool): 
    step = max(1, round(bot * LOADING_BAR_CONSTANT))
    if top % step == 0 or top == bot:
        loadingBarStr = loadingBar(top, bot)
        msg('{} {}.'.format(loadingBarStr, item), quietMode, True)
    return


def export_file(feature_list: List, full_path: str, frame: int):
    if len(feature_list) == 0:
        return
    feature_collection = FeatureCollection(feature_list)
    json_string = dumps(feature_collection)
    save_path = os.path.join(full_path, str(frame) + '.json')
    ensure_directory_exists(save_path)
    with open(save_path, 'w') as out_file:
        out_file.write(json_string)
    return


def ensure_directory_exists(path: str):
    # Creates directory in path if it doesn't exist
    # path can include filename
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)