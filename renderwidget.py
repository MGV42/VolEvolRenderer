from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtWidgets import QWidget, QOpenGLWidget
from PySide2.QtGui import QMouseEvent
from raycaster import VolumeRaycaster

class VolumeRenderWidget(QOpenGLWidget):
    def __init__(self, renderer : VolumeRaycaster, parent : QWidget = None):
        super().__init__(parent)
        self.renderer = renderer
        self.mouseX = 0
        self.mouseY = 0

    def initializeGL(self):
        self.renderer.initialize()

    def paintGL(self):
        self.renderer.render()

    def resizeGL(self, w, h):
        self.renderer.resize(w, h)

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
        elif event.buttons() & Qt.RightButton:
            self.renderer.interactZoom(dy)
            self.update()

        self.mouseX = event.x()
        self.mouseY = event.y()

    @Slot()
    def updateTransFunc(self):
        self.renderer.updateTransFunc()
        self.update()
        


    
        


