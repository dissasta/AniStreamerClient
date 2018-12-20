import sys
import os
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QLabel
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QTimer, QSize
import ctypes

server = '129.228.74.105'
port = '666'

class DropZone(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.fadeOffTime = 30
        self.width = 250
        self.height = 100
        self.left = ctypes.windll.user32.GetSystemMetrics(0) - self.width - 20
        self.top = ctypes.windll.user32.GetSystemMetrics(1) - self.height - 40
        self.initUI()

    def initUI(self):
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.Tool|Qt.WindowStaysOnTopHint)
        bgImage = QtGui.QImage("dropzone.png")
        bgImage = bgImage.scaled(QSize(self.width, self.height))
        p = self.palette()
        p.setBrush(10, QtGui.QBrush(bgImage))
        #p.setColor(self.backgroundRole(), Qt.darkGray)
        self.setPalette(p)
        self.setAcceptDrops(True)

    def hideSelf(self):
        self.counter = 0
        def handler():
            self.counter += 1
            print(self.counter)
            if self.counter >= self.fadeOffTime * 100:
                self.setWindowOpacity(self.windowOpacity()-0.002)
                if self.windowOpacity() <= 0:
                    self.setVisible(False)
                    self.timer.stop()
                    self.timer.deleteLater()
        self.timer = QTimer()
        self.timer.timeout.connect(handler)
        self.timer.start(10)

    def enterEvent(self, e):
         self.setWindowOpacity(0.95)
         self.timer.stop()
         self.timer.deleteLater()

    def leaveEvent(self, e):
        self.hideSelf()

    def closeEvent(self, e):
        e.ignore()
        self.hide()

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
        self.initIcon()
        self.initDropZone()
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

    def initIcon(self):
        self.sysTray = QtWidgets.QSystemTrayIcon(self)
        self.sysTray.setIcon(QtGui.QIcon('icon.png'))
        self.sysTrayMenu = QtWidgets.QMenu(self)
        #showAction = QtWidgets.QAction("Show", self)
        showAction = self.sysTrayMenu.addAction("Show")
        showAction.triggered.connect(self.mainPopUp)
        self.sysTray.setContextMenu(self.sysTrayMenu)
        self.sysTray.activated.connect(self.onTrayIconActivated)
        self.sysTray.show()
        self.sysTray.setVisible(False)

    def initDropZone(self):
        self.dropZone = DropZone()

    def onTrayIconActivated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            print('double')
            self.mainPopUp()
        elif reason == QtWidgets.QSystemTrayIcon.Context:
            pass
        elif reason == QtWidgets.QSystemTrayIcon.MiddleClick:
            pass
        else:
            if not self.dropZone.isVisible():
                self.dropZonePopUp()

    def mainPopUp(self):
        self.show()
        self.dropZone.counter = 0
        self.sysTray.setVisible(False)

    def dropZonePopUp(self):
        self.dropZone.setWindowOpacity(0.95)
        self.dropZone.show()
        self.dropZone.hideSelf()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        for f in files:
            print(os.path.isdir(f))

    def closeEvent(self, e):
        e.ignore()
        self.hide()
        self.sysTray.setVisible(True)

    def exit(self):
        sys.exit()

    def makeConnection(self):
        print('trying to connect')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())