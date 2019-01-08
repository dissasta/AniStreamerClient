import os
from distutils.spawn import find_executable
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QLabel
from PyQt5 import QtGui

def toolCheck(exeFile):
    return find_executable(exeFile) is not None

class Config(QMainWindow):
    tempDir = 'd:\\WORKSPACE\\TEMP'
    outputDir = 'd:\\WORKSPACE\\OUTPUT'
    def __init__(self, mainApp):
        super().__init__()
        self.title = 'Config'
        self.left = mainApp.geometry().left() + 20
        self.top = mainApp.geometry().top() + 20
        self.width = 300
        self.height = 500
        self.userName = None
        self.serverIP = '129.228.74.105'
        self.serverPort = '666'
        self.outputFolder = ''
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setFixedSize(self.width, self.height)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(60, 63, 65))
        self.setPalette(p)
        logo = QLabel(self)
        pixmap = QtGui.QPixmap('logo.png')
        logo.setPixmap(pixmap)
        logo.setGeometry(24, 16, 255,63)
        self.setWindowIcon(QtGui.QIcon('icon.png'))

    def showEvent(self, e):
        e.ignore
