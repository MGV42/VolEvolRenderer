import numpy as np
from PySide2.QtWidgets import QWidget, QColorDialog
from PySide2.QtGui import QMouseEvent, QKeyEvent, QPaintEvent, QResizeEvent
from PySide2.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient, QPalette
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtCore import Qt, Signal, Slot
from transfunc import TransFunc
import glm

class TransFuncWidget(QWidget):

    # global properties
    splineColor = QColor(0, 0, 0)
    splineThickness = 2.0
    splineBrush = QBrush(splineColor, Qt.BrushStyle.SolidPattern)
    splinePen = QPen(splineBrush, splineThickness, Qt.PenStyle.SolidLine)
    
    cpFillColor = QColor(200, 200, 200)
    cpOutlineColor = QColor(127, 127, 127)
    cpOutlineThickness = 2.0
    cpDiameter = 20.0
    cpRadius = cpDiameter / 2
    cpBrush = QBrush(cpFillColor, Qt.BrushStyle.SolidPattern)
    cpPen = QPen(cpOutlineColor, cpOutlineThickness, Qt.PenStyle.SolidLine)

    drawSampleFillColor = QColor(255, 0, 0)
    drawSampleOutlineColor = QColor(128, 0, 0)
    drawSampleOutlineThickness = 1.0
    drawSampleDiameter = 4.0
    drawSampleRadius = drawSampleDiameter/2
    drawSampleBrush = QBrush(drawSampleFillColor, Qt.BrushStyle.SolidPattern)
    drawSamplePen = QPen(drawSampleOutlineColor, drawSampleOutlineThickness, Qt.PenStyle.SolidLine)

    # signals
    transFuncChanged = Signal()

    def __init__(self, spline : TransFunc, parent : QWidget = None):
        super().__init__(parent)
        self.setWindowTitle('TransFunc')
        self.setMinimumSize(200, 200)
        self.spline = spline
        self.leftPressedCPIdx = -1 # index of selected control point
        self.noSamples = 64
        self.mouseX = 0
        self.mouseY = 0
        self.backgroundImage = self.generateBackgroundImage()
        
    def sizeHint(self):
        return super().sizeHint()
    
    def generateCheckerPattern(self, w, h, n, m, grayVal):
        i = np.arange(0, w*h, 1)
        return (255 - (255-grayVal)*(((i//w)//m + (i%w)//n) % 2)).astype(np.uint8)

    def generateBackgroundImage(self):
        w = self.width()
        h = self.height()
        n = 16
        m = 16
        pattern = self.generateCheckerPattern(w, h, n, m, 230)
        backImg = QImage(pattern, w, h, w, QImage.Format_Grayscale8)
        return QPixmap.fromImage(backImg)

    def mapToDrawArea(self, point : glm.vec2):
        return glm.vec2(point.x * self.width(), self.height() * (1.0 - point.y))

    def mapListToDrawArea(self, pointList):
        return [self.mapToDrawArea(p) for p in pointList]

    def mapFromDrawArea(self, point : glm.vec2):
        return glm.vec2(point.x / self.width(), 1.0 - point.y / self.height())

    def mapListFromDrawArea(self, pointList):
        return [self.mapFromDrawArea(p) for p in pointList]

    def QColorFromVec4(self, v : glm.vec4):
        return QColor(int(255*v.r), int(255*v.g), int(255*v.b), int(255*v.a))

    def QColorFromVec3(self, v : glm.vec3):
        return QColor(int(255*v.r), int(255*v.g), int(255*v.b))

    def Vec3FromQColor(self, col : QColor):
        return glm.vec3(col.redF(), col.greenF(), col.blueF())

    def paintEvent(self, event : QPaintEvent):
        painter = QPainter()
        
        drawSamples = self.spline.samplesForDrawing(64)

        drawPointsUnmapped = [sample.xa() for sample in drawSamples]
        drawPoints = self.mapListToDrawArea(drawPointsUnmapped)
        drawColors = [self.QColorFromVec4(sample.rgba) for sample in drawSamples]

        #evenSamples = self.spline.sampleEvenX(self.noSamples)
        #evenPoints = self.mapListToDrawArea([glm.vec2(sample.x, sample.rgba.a) for sample in evenSamples])
        #evenColors = [sample.rgba.rgb for sample in evenSamples]
        
        cpPositions = [p.xa() for p in self.spline.cp]
        cpPositions = self.mapListToDrawArea(cpPositions)
        cpColors = [self.QColorFromVec3(p.rgba.rgb) for p in self.spline.cp]

        # create fill of draw area from control point colors
        horizColorGrad = QLinearGradient(0, 0, self.width(), 0)
        for p, col in zip(drawPointsUnmapped, drawColors):
            horizColorGrad.setColorAt(p.x, col)
        
        verticalAlphaGrad = QLinearGradient(0, self.height(), 0, 0)
        noGradSamples = 10
        gradStep = 1/noGradSamples
        gradPositions = np.arange(0, 1 + gradStep, gradStep)
        gradValues = (255 * TransFunc.smoothstep_1(gradPositions)).astype(int)
        for gradPos, gradVal in zip(gradPositions, gradValues):
            verticalAlphaGrad.setColorAt(gradPos, QColor(255, 255, 255, gradVal))
        
        imgGradFill = QImage(self.width(), self.height(), QImage.Format_ARGB32_Premultiplied)
        imgGradFill.fill(Qt.transparent)
        painter.begin(imgGradFill)
        painter.fillRect(imgGradFill.rect(), QBrush(horizColorGrad))
        painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.fillRect(imgGradFill.rect(), QBrush(verticalAlphaGrad))
        painter.end()

        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        
        painter.drawPixmap(0, 0, self.backgroundImage)

        painter.drawImage(0, 0, imgGradFill)

        painter.setPen(TransFuncWidget.splinePen)
        
        ## spline using evenPoints
        #for i in range(len(evenPoints)-1):
        #    painter.drawLine(evenPoints[i].x, evenPoints[i].y, 
        #                     evenPoints[i+1].x, evenPoints[i+1].y)
        
        # spline using drawPoints
        for i in range(len(drawPoints)-1):
            painter.drawLine(drawPoints[i].x, drawPoints[i].y, 
                             drawPoints[i+1].x, drawPoints[i+1].y)

        ## vertical sample lines
        #painter.setPen(QPen(QColor(0, 0, 255)))
        #for i in range(len(evenPoints)):
        #    painter.drawLine(evenPoints[i].x, self.height(), evenPoints[i].x, evenPoints[i].y)

        # control points
        painter.setPen(TransFuncWidget.cpPen)
        for pos, col in zip(cpPositions, cpColors):
            TransFuncWidget.cpBrush.setColor(col)    
            painter.setBrush(TransFuncWidget.cpBrush)
            painter.drawEllipse(pos.x - self.cpRadius, pos.y - self.cpRadius, self.cpDiameter, self.cpDiameter)

        ## draw points
        #painter.setPen(TransFuncWidget.drawSamplePen)
        #painter.setBrush(TransFuncWidget.drawSampleBrush)
        #for dp in drawPoints:
        #    painter.drawEllipse(dp.x - self.drawSampleRadius, dp.y - self.drawSampleRadius,
        #                        self.drawSampleDiameter, self.drawSampleDiameter)

        painter.end()

    def keyPressEvent(self, event : QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.close()

    def findControlPointAt(self, x, y):
        for i in range(len(self.spline.cp)):
            cpw = self.mapToDrawArea(self.spline.cp[i].xa())
            if (x - cpw.x)**2 + (y - cpw.y)**2 < self.cpRadius**2:
                return i
        return -1

    def mousePressEvent(self, event : QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.mouseX = event.x()
            self.mouseY = event.y()
            self.leftPressedCPIdx = self.findControlPointAt(event.x(), event.y())

            if event.modifiers() & Qt.ControlModifier: # if Ctrl is pressed
                if self.leftPressedCPIdx > -1: # if pressed over a control point, remove it
                    self.spline.removeCP(self.leftPressedCPIdx)
                    self.leftPressedCPIdx = -1
                    self.updateTransFunc()
                else: # if pressed outside a control point, add a new control point
                    xa = self.mapFromDrawArea(glm.vec2(event.x(), event.y()))
                    newCPColor = self.QColorFromVec3(TransFunc.defaultCPColor)
                    # if shift is also pressed, prompt user to set color, else add a cp with default color
                    if event.modifiers() & Qt.ShiftModifier:
                        chosenColor = QColorDialog.getColor(newCPColor, self)
                        if chosenColor.isValid():
                            newCPColor = chosenColor
                    self.leftPressedCPIdx = self.spline.addCP(xa.x, glm.vec4(self.Vec3FromQColor(newCPColor), xa.y))
                    self.updateTransFunc()
   
    def mouseReleaseEvent(self, event : QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.leftPressedCPIdx = -1
        elif event.button() == Qt.RightButton:
            rightPressedCPIdx = self.findControlPointAt(event.x(), event.y())
            if rightPressedCPIdx > -1:
                rightPressedCPColor = self.spline.cp[rightPressedCPIdx].rgba.rgb
                rightPressedCPColor = self.QColorFromVec3(rightPressedCPColor)
                chosenColor = QColorDialog.getColor(rightPressedCPColor, self)
                if chosenColor.isValid():
                    self.spline.cp[rightPressedCPIdx].rgba.rgb = self.Vec3FromQColor(chosenColor)
                    self.updateTransFunc()

    def mouseMoveEvent(self, event : QMouseEvent):
        if event.buttons() & Qt.LeftButton:
            if self.leftPressedCPIdx > -1:
                dx = event.x() - self.mouseX
                dy = event.y() - self.mouseY
                cpda = self.mapToDrawArea(self.spline.cp[self.leftPressedCPIdx].xa())
                if cpda.x + dx >= 0 and cpda.x + dx < self.width(): cpda.x += dx
                if cpda.y + dy >= 0 and cpda.y + dy < self.height(): cpda.y += dy

                xa = self.mapFromDrawArea(cpda)
                self.spline.cp[self.leftPressedCPIdx].x = xa.x
                self.spline.cp[self.leftPressedCPIdx].rgba.a = xa.y
                
                # update control points if they overlap on x
                for i in range(self.leftPressedCPIdx):
                    if self.spline.cp[self.leftPressedCPIdx].x < self.spline.cp[i].x:
                        self.spline.cp[i].x = self.spline.cp[self.leftPressedCPIdx].x

                for i in range(self.leftPressedCPIdx + 1, len(self.spline.cp)):
                    if self.spline.cp[self.leftPressedCPIdx].x > self.spline.cp[i].x:
                        self.spline.cp[i].x = self.spline.cp[self.leftPressedCPIdx].x

                self.updateTransFunc()

            self.mouseX = event.x()
            self.mouseY = event.y()

    def resizeEvent(self, event : QResizeEvent):
        # important: when resizing procedurally-generated images make sure to update the bytesPerLine parameter!!!
        # also important: when painting on a QImage make sure to initialze the color values of the QImage using .fill(...)
        self.backgroundImage = self.generateBackgroundImage()

    def updateTransFunc(self):
        self.update()
        self.transFuncChanged.emit()
        
        
        
        
        

            


