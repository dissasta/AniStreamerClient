from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtGui

class Config(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'Config'
        self.left = 1000
        self.top = 300
        self.width = 300
        self.height = 500
        self.userName = None
        self.serverIP = '129.228.74.105'
        self.serverPort = '666'
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setFixedSize(self.width, self.height)
        self.setWindowFlags(Qt.Tool)

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.gray)
        self.setPalette(p)
        self.setWindowIcon(QtGui.QIcon('icon.png'))