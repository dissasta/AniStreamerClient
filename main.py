import sys
import os
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QLabel
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

server = '129.228.74.105'
port = '666'

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = 'AniStreamer Client'
        self.left = 200
        self.top = 300
        self.width = 800
        self.height = 500
        self.initUI()
        self.initBAR()
        self.createTrayIcon()
        self.makeConnection()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.gray)
        self.setPalette(p)
        self.setAcceptDrops(True)
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.show()

    def initBAR(self):
        bar = self.menuBar()
        fileMenu = bar.addMenu('File')

        connectAction = QtWidgets.QAction('Connect', self)
        fileMenu.addAction(connectAction)
        connectAction.triggered.connect(self.makeConnection)

        exitAction = QtWidgets.QAction('Exit', self)
        fileMenu.addAction(exitAction)
        exitAction.triggered.connect(self.exit)

    def createTrayIcon(self):
        self.sysTray = QtWidgets.QSystemTrayIcon(self)
        self.sysTray.setIcon(QtGui.QIcon('icon.png'))
        self.sysTray.setVisible(True)
        self.sysTrayMenu = QtWidgets.QMenu(self)
        act = self.sysTrayMenu.addAction("FOO")

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        for f in files:
            print(os.path.isdir(f))

    def exit(self):
        sys.exit()

    def makeConnection(self):
        print('trying to connect')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())