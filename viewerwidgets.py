from PySide2.QtCore import Qt, QSize, Signal, Slot
from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtGui import QMouseEvent, QResizeEvent
from renderer import VolumeRenderer
import numpy as np
from converters import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib import ticker

class SimpleImageViewer(QLabel):
    format = {
            1 : QImage.Format_Grayscale8,
            2 : QImage.Format_Grayscale16,
            4 : QImage.Format_RGBA8888
            }
    
    def __init__(self, parent : QWidget = None):
        super().__init__('', parent)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setMinimumSize(50, 50)
    
    def loadQImage(self, img : QImage, flipVertical = True):
        img = img.scaled(self.width(), self.height(), 
                         Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if flipVertical:
            self.setPixmap(QPixmap.fromImage(img.mirrored()))
        else:
            self.setPixmap(QPixmap.fromImage(img))

    def loadImageData(self, imgData, imgDims, flipVertical = True):
        '''
        imgData can be a bytes array or a numpy array
        imgDims should be a list or tuple of 3 ints
        '''
        w, h, d = imgDims
        img = QImage(imgData, w, h, w*d, self.format[d])
        self.loadQImage(img, flipVertical)
        
class VolumeImageViewer(SimpleImageViewer):
    '''
    viewer useful for representing an offscreen image rendered by a VolumeRenderer
    that also supports mouse/keyboard interaction
    '''
    viewChanged = Signal()

    def __init__(self, renderer : VolumeRenderer, parent : QWidget = None):
        super().__init__(parent)
        self.renderer = renderer
        self.update()
    
    def update(self):
        self.renderer.render()
        imgData = self.renderer.getPixels()
        self.loadImageData(imgData, [self.renderer.w, self.renderer.h, 4])
        super().update()

    # TODO: in the future, do not change the w, h parameters of the renderer, 
    # instead scale the rendered image to fit the widget size
    def resizeEvent(self, event):
        self.renderer.resize(self.width(), self.height())
        self.update()

    def mousePressEvent(self, event):
        self.mouseX = event.x()
        self.mouseY = event.y()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.mouseX
        dy = event.y() - self.mouseY

        if event.buttons() & Qt.LeftButton:
            if event.modifiers() & Qt.ControlModifier: # Ctrl pressed
                self.renderer.interactPan(dx, dy)
            else:
                self.renderer.interactRotate(dx, dy)
            self.update()
            self.viewChanged.emit()
        elif event.buttons() & Qt.RightButton:
            self.renderer.interactZoom(dy)
            self.update()
            self.viewChanged.emit()

        self.mouseX = event.x()
        self.mouseY = event.y()

    @Slot()
    def updateTransFunc(self):
        self.renderer.updateTransFunc()
        self.update()

    @Slot()
    def updateAlphaTransFunc(self):
        self.renderer.updateAlphaTransFunc()
        self.update()

class HistogramPlotter(FigureCanvasQTAgg):
    defaultDPI = 100
    def __init__(self, width = 400, height = 200, parent : QWidget = None):
        self.fig = Figure(figsize = (width / self.defaultDPI, 
                                     height / self.defaultDPI), 
                                     dpi = self.defaultDPI)
        self.fig.set_tight_layout(True)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setMinimumSize(50, 50)

        self.xRange = [0.0, 1.0]
        self.yRange = [0.0, 0.01]


    def updateHist(self, histVals):
        
        xVals = np.arange(self.xRange[0], self.xRange[1], 
                          (self.xRange[1] - self.xRange[0])/len(histVals))
        #hVals = hVals / sum(histVals)
        self.axes.cla()
        self.axes.plot(xVals, histVals)
        histMean = (np.max(histVals) - np.min(histVals)) / 2
        self.axes.plot([0, 1], [histMean, histMean])
        chi2 = np.sum((histVals - histMean)**2)/histMean
        self.axes.annotate(f'chi2 = {round(chi2, 3)}', (self.xRange[0] + 0.02, self.yRange[1] - 0.001))

        self.axes.set_xlim(self.xRange)
        self.axes.set_ylim(self.yRange)

        self.fig.canvas.draw()


class GradMapViewer(QWidget):
    def __init__(self, parent : QWidget = None):
        super().__init__(parent)
        self.imgWidget = SimpleImageViewer()
        imgSizePolicy = self.imgWidget.sizePolicy()
        imgSizePolicy.setVerticalStretch(1)
        self.imgWidget.setSizePolicy(imgSizePolicy)
        
        self.histWidget = HistogramPlotter()
        histSizePolicy = self.histWidget.sizePolicy()
        histSizePolicy.setVerticalStretch(1)
        self.histWidget.setSizePolicy(histSizePolicy)
        
        layout = QVBoxLayout()
        layout.addWidget(self.imgWidget)
        layout.addWidget(self.histWidget)
        self.setLayout(layout)

    def updateContents(self, gradMap, histVals):
        w, h = gradMap.shape
        self.imgWidget.loadImageData(gradMap, [w, h, 1])
        self.histWidget.updateHist(histVals)
        self.update()



        


    






