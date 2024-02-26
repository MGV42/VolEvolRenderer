import sys
from PySide2.QtWidgets import QApplication
from dataset import VolumeDataset
from mainwindow import VEMainWindow

if __name__ == '__main__':
    
    app = QApplication(sys.argv)

    dataFile = 'buckyball_64x64x64x1.vol'
    dataset = VolumeDataset(dataFile, 64, 64, 64, 1, True, True, 28)
    
    mw = VEMainWindow(dataset)
    mw.show()
    
    app.exec_()
