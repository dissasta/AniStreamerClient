import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QSpacerItem
from PyQt5 import QtGui
from distutils.spawn import find_executable

def toolCheck(exeFile):
    return find_executable(exeFile) is not None
print(os.getcwd())
ffmpegPresent = toolCheck('ffmpeg.exe')
unRARPresent = toolCheck('UnRAR.exe')
sevenZipPresent = toolCheck('7z.exe')
serverIP = '192.168.0.33'
serverPort = 6666
buffSize = 1024
tempDir = os.path.join(os.getcwd(), "TEMP")
outputDir = os.path.join(os.getcwd(), "OUTPUT")
extendAni = True
aniQFactor = 1
pngCompressionLevel = 100
movCompressionLevel = 2000

class Config(QMainWindow):
    def __init__(self, xy):
        QMainWindow.__init__(self)
        self.title = 'Config'
        self.left = xy[0] + 20
        self.top = xy[1] + 20
        self.width = 300
        self.height = 500
        self.userName = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setFixedSize(self.width, self.height)
        self.setAutoFillBackground(True)
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(60, 63, 65))
        self.setPalette(p)
        logo = QLabel(self)
        pixmap = QtGui.QPixmap('logo.png')
        logo.setPixmap(pixmap)
        logo.setGeometry(24, 16, 255,63)
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.lay = QVBoxLayout(self.centralWidget)
        self.lay.setAlignment(Qt.AlignTop)
        self.layTop = QVBoxLayout(self.centralWidget)
        self.layTop.setAlignment(Qt.AlignHCenter)
        self.layBottom = QHBoxLayout(self.centralWidget)
        self.layBottom.setAlignment(Qt.AlignHCenter)
        self.layTop.addWidget(logo)
        self.lay.addLayout(self.layTop)
        self.lay.addLayout(self.layBottom)

        font = QtGui.QFont('SansSerif', 12)
        font.setBold(True)

        self.horizSpacer = QSpacerItem(28, 0)
        self.vertSpacer = QSpacerItem(0, 400)
        self.layTop.addItem(self.vertSpacer)
        self.toolLabels =  [QLabel(x) for x in ["FFmpeg", "unRAR", "7-Zip"]]
        [x.setFont(font) for x in self.toolLabels]
        [x.setFixedWidth(75) for x in self.toolLabels]
        self.layBottom.addItem(self.horizSpacer)
        for i in range(len(self.toolLabels)):
            self.layBottom.addWidget(self.toolLabels[i])
            self.layBottom.addItem(self.horizSpacer)

        if ffmpegPresent:
            self.toolLabels[0].setStyleSheet("color: green")
        else:
            self.toolLabels[0].setStyleSheet("color: red")

        if unRARPresent:
            self.toolLabels[1].setStyleSheet("color: green")
        else:
            self.toolLabels[1].setStyleSheet("color: red")

        if sevenZipPresent:
            self.toolLabels[2].setStyleSheet("color: green")
        else:
            self.toolLabels[2].setStyleSheet("color: red")

    def showEvent(self, e):
        e.ignore
