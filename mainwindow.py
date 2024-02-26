from PySide2.QtCore import Qt, QSize, Signal, Slot
from PySide2.QtWidgets import QMainWindow, QWidget, QDockWidget
from PySide2.QtGui import QKeyEvent, QFocusEvent
from transfunc import TransFunc
from dataset import VolumeDataset
from raycaster import VolumeRaycaster
from transfuncwidget import TransFuncWidget
from renderwidget import VolumeRenderWidget

class VEMainWindow(QMainWindow):
    def __init__(self, dataset):
        super().__init__()
        self.dataset = dataset
        self.transFunc = TransFunc()
        self.renderer = VolumeRaycaster(self.dataset, self.transFunc)
        self.transFuncWidget = TransFuncWidget(self.renderer.transFunc)
        self.renderWidget = VolumeRenderWidget(self.renderer)
        self.setWindowTitle('VolEvol Renderer')
        self.setCentralWidget(self.renderWidget)

        self.transFuncWidgetDock = QDockWidget('Transfer function')
        self.transFuncWidgetDock.setWidget(self.transFuncWidget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.transFuncWidgetDock)

        self.transFuncWidget.transFuncChanged.connect(self.renderWidget.updateTransFunc)

        self.setFocusPolicy(Qt.StrongFocus)

    def sizeHint(self):
        return QSize(800, 600)

    def updateShader(self):
        self.renderer.rebuildShader()
        self.renderWidget.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R and event.modifiers() & Qt.ControlModifier:
            # update shader when Ctrl+R is pressed
            self.updateShader()

    def focusInEvent(self, event : QFocusEvent):
        # update shader when main window gains focus
        self.updateShader()


    









    







        
