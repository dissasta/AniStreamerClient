import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QSpacerItem, QLineEdit, QCheckBox
from PyQt5 import QtGui
from distutils.spawn import find_executable

def toolCheck(exeFile):
    return find_executable(exeFile) is not None

ffmpegPresent = toolCheck('ffmpeg.exe')
unRARPresent = toolCheck('UnRAR.exe')
sevenZipPresent = toolCheck('7z.exe')
serverIP = '192.168.0.33'
serverPort = 6666
buffSize = 1024
appDir = os.getcwd()
imageDir = os.path.join(appDir, "Images")
tempDir = os.path.join(appDir, "TEMP")
outputDir = os.path.join(appDir, "OUTPUT")
extendAni = True
aniQFactor = 1
pngCompressionLevel = 100
movCompressionLevel = 2000

class Config(QMainWindow):
    def __init__(self, xy):
        QMainWindow.__init__(self)
        self.title = 'SETTINGS'
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
        self.setWindowIcon(QtGui.QIcon(os.path.join(imageDir,'icon.png')))

        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(60, 63, 65))
        self.setPalette(p)
        logo = QLabel(self)
        pixmap = QtGui.QPixmap(os.path.join(imageDir,'logo.png'))
        logo.setPixmap(pixmap)
        logo.setFixedSize(logo.sizeHint())

        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.lay = QVBoxLayout(self.centralWidget)
        self.lay.setAlignment(Qt.AlignTop)
        self.layTop = QVBoxLayout(self.centralWidget)
        self.layTop.setAlignment(Qt.AlignHCenter)
        self.layBottom = QHBoxLayout(self.centralWidget)
        self.layBottom.setAlignment(Qt.AlignHCenter)
        self.vertSpacer = QSpacerItem(0, 12)
        self.horizSpacer = QSpacerItem(28, 0)
        self.layTop.addItem(self.vertSpacer)
        self.layTop.addWidget(logo)
        self.lay.addLayout(self.layTop)
        self.lay.addLayout(self.layBottom)

        font = QtGui.QFont('SansSerif', 10)

        #TOP LAYOUT
        self.vertSpacer = QSpacerItem(0, 20)
        self.layTop.addItem(self.vertSpacer)
        self.options = [(QLabel(x), QLineEdit(y)) for (x,y) in [('Server IP:', '192.168.0.33'), ('Temp Folder:', tempDir), ('Output Folder:', outputDir), ('ANI Qfactor:', str(aniQFactor)), ('PNG Compression lvl:', str(pngCompressionLevel)), ('MOV Compression lvl:', str(movCompressionLevel))]]
        self.vertSpacer = QSpacerItem(0, 4)
        for i in range(len(self.options)):
            lay = QHBoxLayout(self.centralWidget)
            self.options[i][0].setFont(font)
            self.options[i][0].setStyleSheet("color: grey")
            self.options[i][1].setCursorPosition(0)
            self.options[i][1].setStyleSheet("background-color: rgb(66, 67, 69); color: grey;")
            lay.addWidget(self.options[i][0])
            self.layTop.addItem(self.vertSpacer)
            lay.addWidget(self.options[i][1])
            self.layTop.addLayout(lay)

        self.layTop.addItem(self.vertSpacer)

        lay = QHBoxLayout(self.centralWidget)
        self.extendANILabel = QLabel('Extend ANI:')
        self.extendANILabel.setFont(font)
        self.extendANILabel.setStyleSheet("color: grey")
        lay.addWidget(self.extendANILabel)
        self.extendANIBtn = QCheckBox()
        self.extendANIBtn.setChecked(True)
        self.extendANIBtn.setStyleSheet("background-color: rgb(66, 67, 69);")
        lay.addWidget(self.extendANIBtn)
        lay.setAlignment(Qt.AlignLeft)
        self.layTop.addLayout(lay)

        self.vertSpacer = QSpacerItem(0, 150)
        self.layTop.addItem(self.vertSpacer)

        #BOTTOM LAYOUT
        self.toolLabels =  [QLabel(x) for x in ["FFmpeg", "unRAR", "7-Zip"]]

        [x.setFont(font) for x in self.toolLabels]
        [x.setFixedWidth(75) for x in self.toolLabels]

        self.layBottom.addItem(self.horizSpacer)

        for i in range(len(self.toolLabels)):
            self.layBottom.addWidget(self.toolLabels[i])
            self.layBottom.addItem(self.horizSpacer)

        if ffmpegPresent:
            self.toolLabels[0].setStyleSheet("color: green")

        if unRARPresent:
            self.toolLabels[1].setStyleSheet("color: green")

        if sevenZipPresent:
            self.toolLabels[2].setStyleSheet("color: green")

    def showEvent(self, e):
        e.ignore
