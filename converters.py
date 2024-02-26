import numpy as np
from PySide2.QtGui import QImage

def nparrayFromQImage(img : QImage, transposed = False):
    # transposed should be True when images are saved column-wise instead of row-wise
    # TODO: handle images which are BGR instead of RGB
    if transposed:
        w = img.height()
        h = img.width()
    else:
        w = img.width()
        h = img.height()
    
    d = img.depth() // 8

    if d == 1: imgShape = (w, h)
    else: imgShape = (w, h, d)

    return np.ndarray(shape = imgShape, dtype = np.uint8, buffer = img.bits()) 

def nparrayFromByteBuffer(buf : bytes):
    return np.frombuffer(buf, dtype = np.uint8)

def byteBufferToImageFile(buff, w, h, outFile):
    img = QImage(buff, w, h, 4*w, QImage.Format_RGBA8888)
    img.mirrored().save(outFile)