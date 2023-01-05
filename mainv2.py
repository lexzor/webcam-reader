import os
import PyQt5
import cv2
import numpy as np
import re
import random as rd
from PyQt5 import uic
from PyQt5.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, QThread, Qt, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QSlider, QTextEdit, QWidget)

LABELH = 0
LABELW = 0

BIG_LABELH = 0
BIG_LABELW = 0

ALBASTRU = [109,125,89,237,0,231]

PAINTER = False

#STILIZARE DREPTUNGHI

MARIME = 15 # in pixeli

RECORDING = False

roi = []
colors = []
savedColors = []

class Thread(QThread):
    changePixmapWeb = pyqtSignal(QImage)
    changePixmapMask = pyqtSignal(QImage)
    changePixmapPainted = pyqtSignal(QImage)
    
    def run(self):
        cap = cv2.VideoCapture(0)
        color = None
        while True:
            ret, frame = cap.read()
            if ret:
                self.changePixmapWeb.emit(resizeFrame(frame, 0))
                secondframe = self.secondFrame(frame)
                self.changePixmapMask.emit(resizeFrame(secondframe, 0))
                frame = self.afisareDreptunghiuri(frame, secondframe)
                for arr in range(1, len(roi)):
                    if len(roi) > 1 or arr >= len(roi):
                        if roi[arr-1][0] != -1 and roi[arr][0] != -1:
                            cv2.line(frame, (roi[arr-1][0], roi[arr-1][1]), (roi[arr][0], roi[arr][1]), savedColors[arr], 3)
                self.changePixmapPainted.emit(resizeFrame(frame, 1))
                
    
    
    def secondFrame(self, frame):
        global data
        low = [data[0],data[2],data[4]]
        high = [data[1],data[3],data[5]]
        
        formatHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        masca = cv2.inRange(formatHSV, np.array(low), np.array(high))
        kernel = np.ones((3,3),np.uint8)
        return cv2.morphologyEx(cv2.morphologyEx(masca, cv2.MORPH_OPEN, kernel), cv2.MORPH_CLOSE, kernel)
    
    def afisareDreptunghiuri(self, mainframe, secondframe):
        contours, hierarchy = cv2.findContours(secondframe, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        global colors
        if len(contours) > 0:
            arii = []
            for c in contours:
                arii.append(cv2.contourArea(c))
            
            maxLoc = arii.index(max(arii))
            x, y, w, h = cv2.boundingRect(contours[maxLoc])
            
            global PAINTER
            if PAINTER == True:
                if len(roi) > 0:
                    if roi[len(roi)-1][0] != x and roi[len(roi)-1][1] != y:
                        roi.append([x,y])
                        savedColors.append(getColor(colors[1]))
                else:
                    roi.append([x,y])
                    savedColors.append(getColor(colors[1]))
                    
                    
            cv2.rectangle(mainframe, (x, y), (x + MARIME, y + MARIME), getColor(colors[0]), 2)
            return mainframe
        else:
            return mainframe

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("design.ui", self)
        self.setWindowTitle("Webcam Printer")
        self.openWeb.clicked.connect(lambda: self.initUI())
        self.togglePainter.clicked.connect(self.togglePainterFunc)
        self.deletePaint.clicked.connect(self.deletePaintFunc)
        self.setKittyImages()
        
    @pyqtSlot(QImage)
    def setImageWeb(self, image):
        self.userWeb.setPixmap(QPixmap.fromImage(image))
        
    @pyqtSlot(QImage)
    def setImageMask(self, image):
        self.webMask.setPixmap(QPixmap.fromImage(image))
        
    @pyqtSlot(QImage)
    def setImagePainted(self, image):
        self.paintedFrame.setPixmap(QPixmap.fromImage(image))
        
    def setKittyImages(self):
        global LABELW, LABELH
        LABELW = self.userWeb.width()
        LABELH = self.userWeb.height()
        global BIG_LABELW, BIG_LABELH
        BIG_LABELW = self.paintedFrame.width()
        BIG_LABELH = self.paintedFrame.height()
        
        kittyImage = cv2.imread('./kitty.jpg')

        self.setImageWeb(resizeFrame(kittyImage, 0))
        self.setImageMask(resizeFrame(kittyImage, 0))
        self.setImagePainted(resizeFrame(kittyImage, 1))
        
        self.paintRGB.setPlainText("0 255 139")
        self.brushRGB.setPlainText("MTCOLOR")
        global colors
        colors = [formatColor("0 255 139"), formatColor("255 0 0")]
            
    def initUI(self):
        global RECORDING
        if RECORDING == True:
            return -1
        
        self.addEvents()
        self.sendValues()
        self.setTrackBarsValue(ALBASTRU)
        
        th = Thread(self)
        th.changePixmapWeb.connect(self.setImageWeb)
        th.changePixmapMask.connect(self.setImageMask)
        th.changePixmapPainted.connect(self.setImagePainted)
        RECORDING = True
        th.start()
        self.show()
        
    def setTrackBarsValue(self, culoare):
        self.lowHSlider.setValue(culoare[0])
        self.highHSlider.setValue(culoare[1])
        self.lowSSlider.setValue(culoare[2])
        self.highSSlider.setValue(culoare[3])
        self.lowVSlider.setValue(culoare[4])
        self.highVSlider.setValue(culoare[5])
    
    def addEvents(self):
        self.lowHSlider.valueChanged.connect(lambda: self.sendValues())
        self.highHSlider.valueChanged.connect(lambda: self.sendValues())
        self.lowSSlider.valueChanged.connect(lambda: self.sendValues())
        self.highSSlider.valueChanged.connect(lambda: self.sendValues())
        self.lowVSlider.valueChanged.connect(lambda: self.sendValues())
        self.highVSlider.valueChanged.connect(lambda: self.sendValues())
    
    def sendValues(self):
        global data
        data = [self.lowHSlider.value(),
                self.highHSlider.value(),
                self.lowSSlider.value(),
                self.highSSlider.value(),
                self.lowVSlider.value(),
                self.highVSlider.value()]
        
        self.lowH.setText("lowH: " + str(self.lowHSlider.value()))
        self.highH.setText("highH: " + str(self.highHSlider.value()))
        self.lowS.setText("lowS: " + str(self.lowSSlider.value()))
        self.highS.setText("highS: " + str(self.highSSlider.value()))
        self.lowV.setText("lowV: " + str(self.lowVSlider.value()))
        self.highV.setText("highV: " + str(self.highVSlider.value()))

    def togglePainterFunc(self):
        global PAINTER, RECORDING
        
        if RECORDING == False:
            return -1
        
        if PAINTER == True:
            PAINTER = False
            self.togglePainter.setText("Enable")
            self.getColors()
            roi[len(roi)-1] = [-1, -1]
            
        elif PAINTER == False:
            PAINTER = True
            self.togglePainter.setText("Disable")
            
    def deletePaintFunc(self):
        global roi, savedColors
        roi.clear()
        savedColors.clear()
                
    def getColors(self):
        brushRGB = self.brushRGB.toPlainText()
        paintRGB = self.paintRGB.toPlainText()
        global colors
        colors = [formatColor(brushRGB), formatColor(paintRGB)]
         
def resizeFrame(frame, ftype):
        rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
        
        if ftype == 0:
            global LABELW, LABELH
            return convertToQtFormat.scaled(LABELW, LABELH, Qt.KeepAspectRatio)
        elif ftype == 1:
            global BIG_LABELW, BIG_LABELH
            return convertToQtFormat.scaled(BIG_LABELW, BIG_LABELH, Qt.KeepAspectRatio)
          
def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = QApplication([])
    gui = App()
    gui.show()
    app.exec()
    
def formatColor(data):
    if not "MTCOLOR" in data:
        data = data.split()
        return (int(data[0]), int(data[1]), int(data[2]))
    else:
        return data
    
def getColor(data):
    if "MTCOLOR" in data:
        R = rd.randrange(0, 255)
        G = rd.randrange(0, 255)
        B = rd.randrange(0, 255)
        culoare = (R,G,B)
    
        return culoare
    else :
        culoare = (int(data[0]), int(data[1]), int(data[2]))
        return culoare
        
if __name__ == "__main__":
    main()