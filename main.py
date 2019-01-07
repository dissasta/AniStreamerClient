import sys, os, ctypes, socket, threading, subprocess
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QLabel, QPushButton, QTreeWidget, QCheckBox, QComboBox, QLineEdit
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QTimer, QSize, QRect
from config import Config, toolCheck
from comms import *
from jobhandler import *

ffmpegPresent = False
serverIP = '192.168.0.33'
serverPort = 6666
buffSize = 1024

"""
TODO:
-7zip implementation
"""

class JobHandlerWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.title = 'JOB IMPORTER'
        self.left = 400
        self.top = 400
        self.width = 1250
        self.height = 800
        #self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setMaximumSize(self.width, self.height)
        self.tree = QTreeWidget(self)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        self.tree.resize(self.width, self.height)
        self.tree.setStyleSheet("QHeaderView::section{background-color: rgb(50, 50, 50); color: grey;}")
        self.tree.setStyleSheet("color: grey; background-color: rgb(60, 63, 65); alternate-background-color: rgb(66, 67, 69)")
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Path", "IN Filename", "Type", "Alpha", "Gaps", "Resolution", "Duration", "Status", "Ingest", "Format", "OUT Filename"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 150)
        for column in range(2,7):
            self.tree.setColumnWidth(column, 68)
        self.tree.setColumnWidth(7, 78)
        self.tree.setColumnWidth(8, 40)
        self.tree.setColumnWidth(9, 130)
        self.setWindowIcon(QtGui.QIcon('import.png'))
        self.show()

    def scanJobs(self, assets):
        self.jobScannerThread = JobScanner(assets)
        self.jobScannerThread.new_signal.connect(self.createEntry)
        self.jobScannerThread.new_signal2.connect(self.updateEntry)
        self.jobScannerThread.start()

    def createEntry(self, o):
        if self.jobScannerThread.allArchives:
            for archive in self.jobScannerThread.allArchives:
                if archive.tempFolderName in o.path:
                    tempPath = os.path.join(Config.tempDir, archive.tempFolderName)
                    tempPath = tempPath.replace('/', '\\')
                    displayPath = o.path.replace(tempPath, "")
                    if not displayPath:
                        displayPath = '\\'
                    newEntry = QTreeWidgetItem([displayPath, "", o.type])
                    archive.widgetItem.addChild(newEntry)
                    break
                else:
                    alreadyIn = False
                    for archive in self.jobScannerThread.allArchives:
                        if archive.tempFolderName in o.path:
                            alreadyIn = True
                            break
                    if not alreadyIn:
                        newEntry = QTreeWidgetItem([o.path, "", o.type])
                        self.tree.addTopLevelItem(newEntry)
                        break
        else:
            newEntry = QTreeWidgetItem([o.path, "", o.type])
            self.tree.addTopLevelItem(newEntry)
            if not o.type == "" and not o.type == "Archive":
                o.widgetItem = newEntry
                ingestCheckbox = QCheckBox()
                ingestCheckbox.setMaximumSize(14, 14)
                o.ingest = ingestCheckbox
                o.ingest.toggled.connect(o.btnstate)
                o.ingest.setEnabled(0)
                self.tree.setItemWidget(o.widgetItem, 8, ingestCheckbox)
                o.format = QComboBox()
                self.tree.setItemWidget(o.widgetItem, 9, o.format)
                o.outFilename = QLineEdit()
                self.tree.setItemWidget(o.widgetItem, 10, o.outFilename)

        o.widgetItem = newEntry
        o.widgetRow = self.tree.topLevelItemCount() - 1
        if o.type == '':
            for job in o.jobs:
                if job.type == 'Still':
                    folderChild = QTreeWidgetItem(["", job.basename, job.type])
                    o.widgetItem.addChild(folderChild)
                    job.widgetItem = folderChild

                if job.type == 'Sequence':
                    folderChild = QTreeWidgetItem(["", job.matrix, job.type])
                    o.widgetItem.addChild(folderChild)
                    job.widgetItem = folderChild

                if job.type == 'Video':
                    folderChild = QTreeWidgetItem(["", job.basename, job.type])
                    o.widgetItem.addChild(folderChild)
                    job.widgetItem = folderChild

                job.ingest = QCheckBox()
                job.ingest.setMaximumSize(14, 14)
                job.ingest.toggled.connect(job.btnstate)
                job.ingest.setEnabled(0)
                self.tree.setItemWidget(job.widgetItem, 8, job.ingest)

                job.format = QComboBox()
                self.tree.setItemWidget(job.widgetItem, 9, job.format)

                job.outFilename = QLineEdit()
                self.tree.setItemWidget(job.widgetItem, 10, job.outFilename)

        self.tree.expandAll()
        self.tree.sortByColumn(0, 0)
        self.tree.sortByColumn(2, 0)

    def updateEntry(self, job, column, text):
        job.widgetItem.setText(column, text)

    def closeEvent(self, e):
        e.ignore()
        self.destroy()

class DropZone(QWidget):
    def __init__(self, mainApp):
        QWidget.__init__(self)
        self.mainApp = mainApp
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
        #p.setColor(self.backgroundRole(), Qt.darkBlue)
        p.setBrush(10, QtGui.QBrush(bgImage))
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

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls() and ffmpegPresent:
            e.accept()
        else:
            e.ignore()

    def initJobHandlerWidget(self):
        self.jobHandlerWidget = JobHandlerWidget()

    def dropEvent(self, e):
        assets = [u.toLocalFile() for u in e.mimeData().urls()]
        self.initJobHandlerWidget()
        self.jobHandlerWidget.scanJobs(assets)

    def closeEvent(self, e):
        e.ignore()
        self.hide()

class Client(QMainWindow):
    socket = None
    def __init__(self):
        super().__init__()

        self.title = 'ANI-STREAMER CLIENT v0.1'
        self.left = 200
        self.top = 300
        self.width = 1250
        self.height = 800
        self.connected = False
        self.socket = None
        self.jobHandlerWidgets = []
        self.initUI()
        self.initBAR()
        self.initIcon()
        self.initDropZone()
        self.initConfigMenu()
        #self.makeConnection()
        self.senderThread = Sender(self.socket)
        self.senderThread.start()
        self.show()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        #self.setFixedSize(self.width, self.height)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(60, 63, 65))
        self.setPalette(p)
        self.setAcceptDrops(True)
        self.setWindowIcon(QtGui.QIcon('icon.png'))

    def initBAR(self):
        bar = self.menuBar()
        bar.setStyleSheet("*{color:grey; background-color:qlineargradient(x1:0, y1:1, x0:1, y1:1, stop: 0 rgb(50, 50, 50), stop: 1 rgb(60, 63, 65))}")
        fileMenu = bar.addMenu('File')
        connectAction = QtWidgets.QAction('Connect', self)
        fileMenu.addAction(connectAction)
        connectAction.triggered.connect(self.makeConnection)
        configAction = QtWidgets.QAction('Config', self)
        fileMenu.addAction(configAction)
        configAction.triggered.connect(lambda: self.configMenu.show())
        exitAction = QtWidgets.QAction('Exit', self)
        fileMenu.addAction(exitAction)
        exitAction.triggered.connect(self.exit)

    def initIcon(self):
        self.sysTray = QtWidgets.QSystemTrayIcon(self)
        self.sysTray.setIcon(QtGui.QIcon('icon.png'))
        self.sysTrayMenu = QtWidgets.QMenu(self)
        showAction = self.sysTrayMenu.addAction("Show")
        showAction.triggered.connect(self.mainPopUp)
        self.sysTray.setContextMenu(self.sysTrayMenu)
        self.sysTray.activated.connect(self.onTrayIconActivated)
        self.sysTray.show()
        self.sysTray.setVisible(False)

    def initConfigMenu(self):
        self.configMenu = Config(self)

    def initDropZone(self):
        self.dropZone = DropZone(self)

    def initJobHandlerWidget(self):
        self.jobHandlerWidgets.append(JobHandlerWidget())
        return self.jobHandlerWidgets[-1]

    def onTrayIconActivated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
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
        print (self.socket)
        self.sysTray.setVisible(False)

    def dropZonePopUp(self):
        self.dropZone.setWindowOpacity(0.95)
        self.dropZone.show()
        self.dropZone.hideSelf()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls() and ffmpegPresent:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        assets = [u.toLocalFile() for u in e.mimeData().urls()]
        widget = self.initJobHandlerWidget()
        widget.scanJobs(assets)

    def closeEvent(self, e):
        e.ignore()
        self.hide()
        self.configMenu.hide()
        self.sysTray.setVisible(True)

    def hideEvent(self, e):
        e.ignore()
        #self.configMenu.hide()

    def exit(self):
        sys.exit()

    def makeConnection(self):
        try:
            print('trying to connect')
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((serverIP, serverPort))
            self.connected = True

        except Exception:
            print('Couldn\'t connect')

if __name__ == '__main__':
    ffmpegPresent = toolCheck('ffmpeg.exe')
    app = QApplication(sys.argv)
    ex = Client()
    sys.exit(app.exec_())