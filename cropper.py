from main import *
from jobhandler import *
from PyQt5.QtWidgets import QLabel, QMainWindow, QApplication, QWidget, QVBoxLayout, QScrollArea, QSlider
from PyQt5.QtGui import QPixmap
import os, time
from PyQt5 import QtCore

class Cropper(QtCore.QThread):
    def __init__(self):
        super().__init__()
        self.content = [x for x in os.listdir('e:\\tools\\anistreamer\\BIG') if x.endswith('.tga')]
        print(len(self.content))
        self.mainWindow = QMainWindow()
        self.mainWindow.setWindowTitle("CROP AREA")
        self.mainWindow.setMaximumSize(1920,1080)
        self.mainWindow.setGeometry(0,0,1920,1080)
        self.centralWidget = QWidget()
        self.mainWindow.setCentralWidget(self.centralWidget)
        self.lay = QVBoxLayout(self.centralWidget)
        self.lay.setAlignment(Qt.AlignTop)
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setMaximumSize(1920,1040)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("PREVIEW")
        self.scrollArea.setEnabled(True)
        self.lay.addWidget(self.scrollArea)
        self.label = QLabel()
        self.scrollArea.setWidget(self.label)

        self.sl = QSlider(Qt.Horizontal)
        self.sl.setMaximumWidth(1500)
        self.sl.setMaximum(len(self.content) - 1)
        self.sl.setValue(0)
        self.sl.setTickPosition(QSlider.TicksBelow)
        self.sl.setTickInterval(1)
        self.lay.addWidget(self.sl)

        self.sl.valueChanged.connect(self.valuechange)

        self.mainWindow.show()

    def valuechange(self):
        position = self.sl.value()
        try:
            pixmap = QPixmap(os.path.join('e:\\tools\\anistreamer\\BIG', self.content[position]))
            self.label.setPixmap(pixmap)
        except Exception:
            print('something went wrong')

    def run(self):
            pixmap = QPixmap(os.path.join('e:\\tools\\anistreamer\\BIG', self.content[0]))
            self.label.setPixmap(pixmap)
