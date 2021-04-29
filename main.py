import sys, os, ctypes, socket, tempfile
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QLabel, QPushButton, QTreeWidget, QCheckBox, QComboBox, QLineEdit, QMessageBox
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QTimer, QSize, QRect, QRectF, QLockFile, QDir
from comms import *
from jobhandler import *
from config import *
from cropper import *

"""
TODO:
-7zip implementation
-Improve folder scanner
-Implement TGA-RLE imports
-Re-implement Alpha scanning using binary headers
-Implement config .ini
-Implement asset splitting into separate outputs
"""

class JobHandlerWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.title = 'JOB IMPORTER'
        self.left = 400
        self.top = 200
        self.width = 1340
        self.height = 800
        #self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.jobsReady = False
        self.jobsDone = False
        self.cropper = None
        self.counter = 0
        #self.setAcceptDrops(True)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setMaximumSize(self.width, self.height)
        self.setAutoFillBackground(True)
        self.createGoButton()
        self.createProgressBar()
        self.tree = QTreeWidget(self)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        self.tree.resize(self.width, self.height-30)
        self.tree.setStyleSheet("QHeaderView::section{background-color: rgb(50, 50, 50); color: rgb(100, 100, 150)};")
        self.tree.setStyleSheet("color: grey; background-color: rgb(60, 63, 65); alternate-background-color: rgb(66, 67, 69); ")
        self.tree.setFocusPolicy(Qt.NoFocus)
        self.tree.setColumnCount(11)
        self.tree.setHeaderLabels(["Path", "IN Filename", "Type", "Alpha", "Gaps", "Resolution", "Duration", "Status", "Ingest", "Crop", "Format", "OUT Filename", ""])
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 150)
        for column in range(2,7):
            self.tree.setColumnWidth(column, 68)
            self.tree.header().setSectionResizeMode(column, QtWidgets.QHeaderView.Fixed)
        self.tree.setColumnWidth(7, 78)
        self.tree.setColumnWidth(8, 40)
        self.tree.setColumnWidth(9, 40)
        self.tree.setColumnWidth(10, 130)
        self.tree.setColumnWidth(11, 186)
        self.tree.setColumnWidth(12, 32)
        for column in range(2,13):
            self.tree.header().setSectionResizeMode(column, QtWidgets.QHeaderView.Fixed)
        self.iconBase64 = b"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"
        self.setWindowIcon(iconFromBase64(self.iconBase64))
        self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tree.header().setSectionsMovable(False)
        self.tree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection | QtWidgets.QAbstractItemView.OnItem)
        self.tree.setFocusPolicy(QtCore.Qt.NoFocus)
        self.show()

    def scanJobs(self, assets):
        self.jobHandlerThread = JobScanner(self, assets)
        self.jobHandlerThread.new_signal.connect(self.createEntry)
        self.jobHandlerThread.new_signal2.connect(self.updateEntry)
        #self.jobHandlerThread.jobsReadySignal.connect(self.updateJobsReady)
        self.jobHandlerThread.progressBar.connect(self.progressBarUpdate)
        self.jobHandlerThread.start()

    def createEntry(self, o):
        if self.jobHandlerThread.allArchives:
            for archive in self.jobHandlerThread.allArchives:
                if archive.tempFolderName in o.path:
                    tempPath = os.path.join(tempDir, archive.tempFolderName)
                    tempPath = tempPath.replace('/', '\\')
                    displayPath = o.path.replace(tempPath, "")
                    if not displayPath:
                        displayPath = '\\'
                    newEntry = QTreeWidgetItem([displayPath, "", o.type])
                    archive.widgetItem.addChild(newEntry)
                    break
                else:
                    alreadyIn = False
                    for archive in self.jobHandlerThread.allArchives:
                        if archive.tempFolderName in o.path:
                            alreadyIn = True
                            break
                    if not alreadyIn:
                        newEntry = QTreeWidgetItem([o.path, "", o.type])
                        self.tree.addTopLevelItem(newEntry)
                        break
        else:
            newEntry = QTreeWidgetItem([o.path, "", o.type])
            newEntry.setFlags(Qt.ItemIsEnabled)
            self.tree.addTopLevelItem(newEntry)
            if not o.type == "" and not o.type == "Archive":
                o.widgetItem = newEntry
                ingestCheckboxlabel = QLabel()
                ingestCheckboxlabel.setMaximumSize(40,22)
                #ingestCheckboxlabel.setStyleSheet("background-color: rgba(0,0,0,0%)")
                o.ingest = QCheckBox(ingestCheckboxlabel)
                o.ingest.setMaximumSize(14, 14)
                o.ingest.move(12, 4)
                o.ingest.toggled.connect(o.btnstate)
                o.ingest.setEnabled(0)
                self.tree.setItemWidget(o.widgetItem, 8, ingestCheckboxlabel)

                o.edit = QPushButton('EDIT', self)
                o.edit.setStyleSheet("background-color: rgb(50, 50, 50); color: grey;")
                o.edit.parent = o
                o.edit.setMinimumWidth(32)
                o.edit.setEnabled(0)
                o.edit.clicked.connect(self.edit)
                self.tree.setItemWidget(o.widgetItem, 9, o.edit)

                o.format = QComboBox()
                o.format.activated.connect(o.toggleRunJobButton)
                o.format.setMaxVisibleItems(14)
                self.tree.setItemWidget(o.widgetItem, 10, o.format)
                o.outFilename = QLineEdit()
                o.outFilename.setEnabled(0)
                o.outFilename.editingFinished.connect(o.toggleRunJobButton)
                o.outFilename.textChanged.connect(o.reverifyFilename)
                self.tree.setItemWidget(o.widgetItem, 11, o.outFilename)

                o.runJob = QPushButton('RUN', self)
                o.runJob.setStyleSheet("background-color: rgb(50, 50, 50); color: grey;")
                o.runJob.setMinimumWidth(32)
                o.runJob.parent = o
                o.runJob.setEnabled(0)
                o.runJob.clicked.connect(self.runJob)
                self.tree.setItemWidget(o.widgetItem, 12, o.runJob)

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

                folderChild.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                ingestCheckboxlabel = QLabel()
                ingestCheckboxlabel.setMaximumSize(40,22)
                #ingestCheckboxlabel.setStyleSheet("background-color: rgba(0,0,0,0%)")
                job.ingest = QCheckBox(ingestCheckboxlabel)
                job.ingest.setMaximumSize(14, 14)
                job.ingest.move(12, 4)
                job.ingest.toggled.connect(job.btnstate)
                job.ingest.setEnabled(0)

                self.tree.setItemWidget(job.widgetItem, 8, ingestCheckboxlabel)

                job.edit = QPushButton('EDIT', self)
                job.edit.setStyleSheet("background-color: rgb(50, 50, 50); color: grey;")
                job.edit.parent = job
                job.edit.setMinimumWidth(32)
                job.edit.setEnabled(0)
                job.edit.clicked.connect(self.edit)
                self.tree.setItemWidget(job.widgetItem, 9, job.edit)

                job.format = QComboBox()
                job.format.activated.connect(job.toggleRunJobButton)
                job.format.setMaxVisibleItems(14)
                self.tree.setItemWidget(job.widgetItem, 10, job.format)

                job.outFilename = QLineEdit()
                job.outFilename.setEnabled(0)
                job.outFilename.textChanged.connect(job.reverifyFilename)
                job.outFilename.editingFinished.connect(job.toggleRunJobButton)
                self.tree.setItemWidget(job.widgetItem, 11, job.outFilename)

                job.runJob = QPushButton('RUN', self)
                job.runJob.setStyleSheet("background-color: rgb(50, 50, 50); color: grey;")
                job.runJob.setMinimumWidth(32)
                job.runJob.setEnabled(0)
                job.runJob.parent = job
                job.runJob.clicked.connect(self.runJob)
                self.tree.setItemWidget(job.widgetItem, 12, job.runJob)

        self.tree.expandAll()
        self.tree.sortByColumn(0, 0)
        self.tree.sortByColumn(2, 0)

    def createGoButton(self):
        self.goButton = QPushButton('RUN ALL', self)
        self.goButton.setStyleSheet("background-color: rgb(50, 50, 50); color: green;")
        self.goButton.move(self.width - 78, self.height - 26)
        self.goButton.setEnabled(1)
        self.goButton.clicked.connect(lambda: self.runAllJobs())

    def createProgressBar(self):
        self.progressBar = QLabel(self)
        self.progressBar.setStyleSheet("background-color: rgb(100, 100, 150);border: 1px inset black")
        self.progressBar.move(10, self.height - 24)
        self.progressBar.setFixedHeight(20)
        self.progressBar.maxW = self.width - 100
        self.progressBar.setFixedWidth(0)
        self.progressBar.setVisible(False)

    def updateJobsReady(self, b):
        if b:
            self.jobsReady = True
            self.goButton.setStyleSheet("background-color: rgb(50, 50, 50);color: green;")
            self.goButton.setEnabled(1)

    def runJob(self):
        job = self.sender().parent
        self.jobHandlerThread.processJob(job)

    def edit(self):
        job = self.sender().parent
        if not self.cropper:
            self.cropper = Cropper(self, job)
        else:
            self.cropper.close()
            self.cropper = Cropper(self, job)

    def runAllJobs(self):
        #self.goButton.setText('WORKING')
        #self.goButton.setStyleSheet("background-color: rgb(50, 50, 50);color: green;")
        self.jobHandlerThread.processAll()

    def progressBarUpdate(self, max, current, visible):
        progress = int(100/(max/current))
        self.progressBar.setVisible(visible)
        if progress <= 100:
            self.progressBar.setFixedWidth((self.progressBar.maxW/100)*progress)

    def updateEntry(self, job, column, text):
        job.widgetItem.setText(column, text)

    def closeEvent(self, e):
        self.close()
        if self.cropper:
            self.cropper.close()
        if self.jobHandlerThread.isRunning():
            self.jobHandlerThread.terminate()
            self.jobHandlerThread.wait()
        for folder in self.jobHandlerThread.tempArchiveFolders:
            if os.path.exists(folder):
                try:
                    shutil.rmtree(folder)
                except Exception:
                    pass

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls() and ffmpegPresent:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        assets = [u.toLocalFile() for u in e.mimeData().urls()]
        for asset in sorted(assets):
            self.jobHandlerThread.assets.append(asset)

class DropZone(QWidget):
    def __init__(self, mainApp):
        QWidget.__init__(self)
        self.mainApp = mainApp
        self.fadeOffTime = 15
        self.width = 375
        self.height = 150
        self.left = ctypes.windll.user32.GetSystemMetrics(0) - self.width - 20
        self.top = ctypes.windll.user32.GetSystemMetrics(1) - self.height - 40
        self.initUI()
        self.jobHandlerWidgets = []

    def initUI(self):
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.Tool|Qt.WindowStaysOnTopHint)
        self.iconBase64 = b"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PSJodHRwOi8vd3d3LmdpbXAub3JnL3htcC8iCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iCiAgIHhtcE1NOkRvY3VtZW50SUQ9ImdpbXA6ZG9jaWQ6Z2ltcDo1Zjk3MGE5YS01MTYyLTRhMGItODY3NC05NzQ1ZTc3ZTU1YTYiCiAgIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6NzZhYzVjY2UtMjE3YS00YWVhLWFmZDEtODNhZTM4ZTkwNzU4IgogICB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6MGQyZjgyYzEtZGIyMi00M2M3LWIxN2UtZTRiZWYzNGUyOTljIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJXaW5kb3dzIgogICBHSU1QOlRpbWVTdGFtcD0iMTU0ODE2OTQzOTIyMDM5NSIKICAgR0lNUDpWZXJzaW9uPSIyLjEwLjQiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICB4bXA6Q3JlYXRvclRvb2w9IkdJTVAgMi4xMCI+CiAgIDxpcHRjRXh0OkxvY2F0aW9uQ3JlYXRlZD4KICAgIDxyZGY6QmFnLz4KICAgPC9pcHRjRXh0OkxvY2F0aW9uQ3JlYXRlZD4KICAgPGlwdGNFeHQ6TG9jYXRpb25TaG93bj4KICAgIDxyZGY6QmFnLz4KICAgPC9pcHRjRXh0OkxvY2F0aW9uU2hvd24+CiAgIDxpcHRjRXh0OkFydHdvcmtPck9iamVjdD4KICAgIDxyZGY6QmFnLz4KICAgPC9pcHRjRXh0OkFydHdvcmtPck9iamVjdD4KICAgPGlwdGNFeHQ6UmVnaXN0cnlJZD4KICAgIDxyZGY6QmFnLz4KICAgPC9pcHRjRXh0OlJlZ2lzdHJ5SWQ+CiAgIDx4bXBNTTpIaXN0b3J5PgogICAgPHJkZjpTZXE+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjY2NTk5NWFjLTJiZjctNDZmMy05MWVmLTJmZDZlMjc1NWI3ZSIKICAgICAgc3RFdnQ6c29mdHdhcmVBZ2VudD0iR2ltcCAyLjEwIChXaW5kb3dzKSIKICAgICAgc3RFdnQ6d2hlbj0iMjAxOS0wMS0yMlQxNTowMzo1OSIvPgogICAgPC9yZGY6U2VxPgogICA8L3htcE1NOkhpc3Rvcnk+CiAgIDxwbHVzOkltYWdlU3VwcGxpZXI+CiAgICA8cmRmOlNlcS8+CiAgIDwvcGx1czpJbWFnZVN1cHBsaWVyPgogICA8cGx1czpJbWFnZUNyZWF0b3I+CiAgICA8cmRmOlNlcS8+CiAgIDwvcGx1czpJbWFnZUNyZWF0b3I+CiAgIDxwbHVzOkNvcHlyaWdodE93bmVyPgogICAgPHJkZjpTZXEvPgogICA8L3BsdXM6Q29weXJpZ2h0T3duZXI+CiAgIDxwbHVzOkxpY2Vuc29yPgogICAgPHJkZjpTZXEvPgogICA8L3BsdXM6TGljZW5zb3I+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz7TO8UUAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAC4jAAAuIwF4pT92AAAAB3RJTUUH4wEWDwM7hWwfpQAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAAw2SURBVHja7Z17bFtXHce/146d2LEdx4mdxHk3TdY06ZouXZ9bKXsIKBvaNFAn8ccGmsqomKBCaIDQkNA0TZqm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"
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(QtCore.QByteArray.fromBase64(self.iconBase64))
        bgImage = QtGui.QImage(pixmap)
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
         self.setWindowOpacity(0.90)
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
        self.jobHandlerWidgets.append(JobHandlerWidget())
        return self.jobHandlerWidgets[-1]

    def dropEvent(self, e):
        assets = [u.toLocalFile() for u in e.mimeData().urls()]
        widget = self.initJobHandlerWidget()
        widget.scanJobs(assets)

    def closeEvent(self, e):
        e.ignore()
        self.hide()

class Client(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = 'ANI-STREAMER CLIENT v0.1'
        self.left = 200
        self.top = 160
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
        self.removeTemps()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        #self.setFixedSize(self.width, self.height)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(60, 63, 65))
        self.setPalette(p)
        self.setAcceptDrops(True)
        self.iconBase64 = b"iVBORw0KGgoAAAANSUhEUgAAAEAAAAA+CAYAAACbQR1vAAAZw3pUWHRSYXcgcHJvZmlsZSB0eXBlIGV4aWYAAHjarZtrduS4joT/axWzBPFNLofPc2YHs/z5glTa6bKrqnvu2N3OdFoSSSAQCICsa/7Pf6/rv/hKLsXLh5RjifHmyxdfbOVNvs/XeTW33z/3l3/+xO9fPr/cfP5g+cjx6s6v8fncVD4Pnzek50mmff38Sv15Tn4eZD4evL+cRtb757r8PMjZ87l5fr/Kc1/1b8t5/rf9eezz8F9/9wljjMDznL3sdMbd/PQaxTEDV1zdr5XfrdU7y3u3P3cu/my76+PtL8Zb+Wfb3fW5wn01xXXH54L4i42ez0345XP34TX7ZUbm9dZ+/UMr+OX96812a4281jyrqz5iqXg9i3qZcL/jQh7i3b4t8p34P/A+7e/Cd2aJHY8NvNn47pcpxmLtZbwZpppl5n7tpjNFb6dNvFrbrdufZZdssX07w+vbLJtww7hcxicdrzk+th9zMXvcssfrJjPyMFxpDQ+TF799Xz99+H/5/njQWoKuMduYeduKeVlhmmnIc/rJVTjErMemYdt3f18fbv38kmMdHgzbzJkF1rudR7RgPrHltp8d14XbX084mzSeB2Aixg5Mxjg8cEfjgonmTtYmY7Bjxj+VmVvnbcMDJgQ7zLXwDbjHOdlqbO5JZl9rgz0fQy04IrjoEq4hUHCW9wH8JJ/BUA0u+CuEEEMKOZRQo4s+hhhjiuKoCmH5FFJMKeVUUs0u+xxyzCnnXHIttjgoLJRY0lVyKaVWBq08unJ35Ypam22u+RZabKnlVlrtwKf7Hnrsqedeeh12uEH4jzjSNfIoo04zgdL0M8w408yzzLrA2nLLr7DiSiuvsuqH1x6vfvWa+cVzf/aaebwmj/l9Xfr0Gh+n9HqEEZ0E+QyPWW/weJIHALSVz+5svLfynHx2F0tQBIvXTJBzhpHH8KCfxoZlPnz36bk/+u0K/l/5zf7Oc5dc9//huUuuezz33W8/eG3UnVHcdpCiUDa93YLYPH+MbU2WtBZDL0JyYJGJ9ebSb82PtDqjr/3I/UlsXSnsrjZXvV6vN++vq8Y0TZ/Z6Ka7dgbwbQ2b9mvzrlf9pXCZXyWxinWtFPtMXJE8xrFjYgLeuFYWXk3Nhg7BxNXcHLoZ45HpZ9f73vJ0zLKGVC87ethPHy0tfNcj5tjLqyMEU1qKLtdB3kut9IapV3Sd50zjZ1rDyxbWMyOt2FX+WlxonRHGXtA6P2cLERoJuDQZn1hTwx+tRFNncqubVXmW9eVqy/TozFwB0g+p15xnjMQAayg1DBJPSWblAf7gJW9676LvEGD9lCaPKxryiq9l9LbybN0dA5dO7mJ2zk2WHh0GWzMAudJWwlrgvsexRmxhMmS6L0ybRyg83acyu1vAoY+xDUuWnefBLEcJxrYyFoBe99SnUyw++772yqWm0docbcbjibZKaC5GDBpLc9w6x7BtEG4xtDzwZ0krVIYzgTQ1cUYal3AQBZ179dimYeTsgThzmywj2tXMKpjB9oZ1Fh+txrJclCNmSBMb3S5di4SXVrw3Rkpm/gAmTUDQ202MMLMB7IcR2tIsAKTe5N/gbQUqMEkOBjdcsFfWGx+kvr6+nnCZw22kOQvSRhvnM1PloxMwCrHrxxiD7PYw76+JqRJt9557s6uzXPmL5TqXtLSW4xCUtnfGDcKSR6IyIpciJfD+PH9jOByTAMoqEfuw6tLaGPLIdVwC8ICHw4jMPwfbAJoNofvQfMYbKz6LBAZztjgHPjUxwUWVmRLvV6vwciOeZoBTE+y8DeSQNKKDKr37l9cy82oX4ROTA5Y2t3tOWJiI7nYdfIv0Hny7d3y3B9/hAwcXczasxChl2dYBKpPOBP2ClkHqwa1WZ5ugULCFY2joqYk+iJIy8qxXWTFoIP4kxoBCDCE3RwCWxc6ckAidzI8yngHaa6Bqj3EYDjYxhCWZtsitA0IIBcjBfBiWJHvDErF2/o+ltnoIFAH3MowA9MbQxNoG0BtFc80bRaOSdct3iiamUIyE7H14k0zLmnnu5hTw0jaLluheKNG4H1xcubGvO68nsA6+dBcioq4PgM3XrY5lTsi+iX+ABFRbwFCFQOsKrXofh2ASyAcSZQAG93OxiMHklSoGA+ZJMTGVMH0hUJOCnUetQkSIwDtsfovGhjUwh4cyy1XDHNZx88KXOBJ2LijlGDNsZOY0//Dz63d/mDgP/JMkcHWYFcgzeM5eSDKgpxIJ6I9IukYR1CtPqwjuCt6e2kBbwEvTAEHMVETtoO5WjljZ4BbD+3bjVt8BNzBsG+9XkMoQsx5n5ylkLg+eCMcQmxPxEhd4zozZbC1oJ9RMMJj+XgH3FmDacL+Bz40gCjieodrbUO8jfY4DGVM/1WZmthuy1wMxU/4CxsOM2PNk/T3Nce6JeaR8qVI2QpA+IuudoPWZ/O1gbpARCW+7k2gUkQ6WuG6l7M0QHfoW8nbKNiwBpiepPioDIMOeQFKpSFVvU/4hDMsM4kkBC2S1UNPdGppghWtqaQ2l2ebqyp9wGmtFnC2HdOystaIwyQS5Tuk6LMVE8ZzkCvk7wZTO5Kvv6cIpPeWGPzX4QMZuMu0tSHfwYlP2diwppQhampSNPIJmSL6B8gvmJ3ut1GZbXUJPlUJAsj42KIkQzdgkVJgMUbOzCEMwlY6PK9pxpF4uch1ZpUvoKJFP5AzjxId4up/t/knUvb06aHUlEiR2jiK5uIaesR20skAOa1AROn5FBYJ7yPtkkw73ET4O8tuzbrLRIQnWtGXKXNtv915WgHOr1tLRaySivD9N5CeYx3rKgQ5EuugdxYZY2Tm2TEE2MSvcjapwUzcBTp+WzLpnAnMgv+OYopA8b1iMIM9KR8tpKR4h69EwFfbaEoQsoUyhnHMWW6SM60LbtIlOB8DclKHJaRiy2esJY6Ut3KtxJe7H0S9bUUvEdB7ZqDL4bwWKCsoynOhBwmw7oabLGRD0L1THD6KDt/e40s6NihlJK/LS1knKjzwtKz9JiT0Rs14R4wYAum0cVhVPxQ9w9jxCGN2BHcp5UFlbDuqBii7YAAO6L0kWigy19UKYjNIjS1MZFEa7qWwMdwWVTXU+iOT2W7HmosLuNvOWcSQY+GBZ2K7LepTrxFAELngBi+7qgEoJeI9JjLpwD4IGZiNGO3wx7SLTBG8YPPf3cLk+48UamHoElCIki/OzAhyRjdCqkH8/JLb5pEASwxYfa2uVAK0dWWMoPhMVYfNLLumFoi+/3+be3lPL+WIGgIx4++PSrfxf14pa9/tCQfz9wr9dd/3TC79ch7wDZxYFjoBSjVTrFWvpaDfUUPMoLmhL+cNLc6oY43okAIqulTm2Tk0KIxiyg6t+WDhDZpfCLxBqFI2Q/NwINqfSaIEcG2xG9BtLsYjQhAsrEKKAf0q/jErcsX19BPcObUQjieloaQW1CoHDDfjHVTQetT+pSGqsQR7txHzwSL8ugLVAsZyYVqYeIhpMCMWsI0QsZOXUSEVzqFiisP5IRaRvwU5e26lIOty9ZGd6ZGd7RcTOrJs+yJ7oVrG15Ycm25VQGyno6qa1E09T1GG+hCX5AgUcLFZBIXliZZJW+09ccL3IgFswaVGJQS1wZAhD7lsIFoC8Ds98sow4plBztnlbqDb7+0UfBqo/5UZcp8rSGnfVT4DjysjqJnantApVAmhki9ovu8wikZb4WWDNUONwJSrN+OXHkA29aiCE/u4VoMWTRCb0DhDJGmI0qHYTKgKQ4nv5g14EJ3KFjAi9kQ7qLuFVTuli0K7MP3uiMo6WRE8GSBib2+8hTmAx8UnQd6TKh4wT+QIhnbellloYajNM0Kl6oTnxi1h+KouIgSQ6bobY9Xfbs8rh3gweqOrWlMyBsIi4YKwLGUihICw4X5olF5NFkG87s52rCctepd88oBt+a3C7yZgESDVNFkf1Y24mqMpEcNO117eL8zOfdObDGB/zcXqMU1+J2cTP2Wgy1z+eDTK6mfunyejv/uo7P+3rz3SeEb4P8NN0Pud+fZ18Tcp2Nin/nKYGHlIXRY2WKjmiLhNP9BOduawZqi3xFhUkiS8Jv2nd6ryg4Bb6GvrPsEXcdejpx9So/gg6LMHuKjX9LhihiETFcAEBKUeuwPNJHcgtJglrIjifBwxtOyAPUyuZQQbiQD1ymGergygRfTnlXGrcREwQy1atroedyUId/flZNiZ7FE0yH1yFejxEB2fHm6yWCZkgVU3ypHTfrid/hS1iMlJbZL/LaTvmlk67uXDYcxt7bWaL4tS+a0fzFIDpvQBEhVmSJHImehJtUlvwK6lcm1WgBtQfKkliDWbaEf9T77GagktEFOqZmbi8z1mNiHwpw+fPrsMXhT5nRsMRoG1TQNqrD8o/8MAuwAyU1wyeu/GahZjByJxKdRRD071MnXjoCE5hLj5CZJQZn95AFxOgNMRHKGxqkcNHm2X0HG5fdcsNRwUFg9iWXwzahCTYHOAE8lk/+Cqo3DWuN01bqcKACm5K8VvH4HtrBQlLclYzQeR7YZGwhfLguWmgpovkYXbymBObkhjDusMGP8L1A+dMchS4G9zGalgaSsBgoXZEImkvnF7cLnZAqeJTDdO7vZCu3oU0E8LCIhXUsKPKrus3mN6S7CfJXkbM8ddFX5/A7xA8iV0OUjd0txTwmALV1YmQl9iWmpz8PSl5q1YgPVAlV6SfjSL3TKJNv61YETxgxIT+ez1+mTq6Cc67WiqlQ70fJe9N9z9nO2LJmniK+10GLpWB15c6kDjZTb2nSIKLKFwxiw9WUrZZN6nGc9qocsaqngynkX2BrvCBroMtQesrsPzfgXXxxnm1R2+VcSPGGwvD76VFKSX8WIMjDbkkkfeqWMWUhMBTxTjo5FLT4BQOzSLX5F6KSiTlDduibpr9BQO/UXbXV2kHR8Rvndtd/5hY/abctXsJyLHZS0Ah8FdUnN/6aEZzIn584gJYUBwR2da1+pudE9I847OMGduFF7507z6ad+P2WTVprmZAciY1a8oDjfIdGtcbNvAqTCJkFPUkUVb5ExgVLUnxRs0CMMxp0mZwnpBCqMV1uY+Y5y51v0V8Er9QUNYzd0+wkO9A1cm+FPKHrvyB1AbU9U5X4Rtd/XO2un5F11dQJWV67YzsLbbUk0A1XbDSwK9lqt3RLtt6NHCSmpnmSd9DLQOpxHjy9638nU7+3kqgnsAQKl+kdMFKSLCTgxU/ZvdjTvx8T8LSJYcTDmV5Zx7cESJv/VeoNTdLHbz3MNQEnsdGqKH7IaRe1VSAkLDzJiQeDvSug71NScOMun5X/c8SyWqKN96Du01dn8Qlr8FcfuB5hK+KjJQ+ivaoyh+23EV7W6evnkT5InWQGwiCTGyR9y7ftY1Dmq6nIwa99j/k3X6WsnbmVftO2AW48Zq7f+LQGTv1wsROxq73bqwgKvbiJI+cNLw9Bj8qHmgUlRlbjdxqliU3yWH2CHmUlj++YeDRRA8UVfKmOxl4i9Bu9ibVeoH22qgliEp0PIKqTo0cs5WOcpxXI5/Kv5x0ZEVRUvhynPbgtugZ2l6dQuEWuIeZyv6JDWYrFcVK4Te1ST0MVawOK+2y76TSWg7iEBGHIcPedmzSLTXskXs5O5DUfYSIthSKcUw+1y0sc1C+I1COhD6KTcZrW6ZramdimtYmr5mxF0rF2kRYw5Xud0NequSfuZ6Zap4KEKbJXNQb99BUVUy+RvvJENfPE33Ns5ictA0l+8T49qxfZ17V84cd1OTVJl9wKR/BtdrbvCDbLGWKco2oyqE9xYCES1vCkVlcv9Sw3Q09JHXqVGuE64Ly9uDStpobFVogt0F14BMNTfhSZojihordRP69CDsQlREJutNGd0jVHBFTG4Kg9trT3RUrLf9O2F9/UEGBguF7g3bebTKy+qFO/PD0AC5EeDamxqX+dQ+7VyyryR3aws2aZxjaXGtWpYEAONZrp3VnaKxDplVjLJAviZGabjgpTlVAv+WlqP3Jvjdgo8oNLG6Ivmtqu83/4ZzBchM66/5wVEjaWzrNISsRpD6jmpWX2irlaasc+7TPVqMxyh7kDVFPJu8rEdUeht97oks71J0kWKlpRy1IeouIcO3ZlFU+/qUhMYcXjbTfFwCXKoAgMiNE7MduLaauI7AwYCF+/pR4nwqv1By1ayaFB0MqT03Vq08i7gAThjmd16wjB6qf9uPb2VtcCkkSYBM9b5Ri60GChM4NZhqumhDwlWmjKZFSnxQCpNkQrBqyXF73XhFTb7NCP9KQqlxIr+HQyFLPip+hVNWqBOWeQyZwCSwChj+quXzjlgWbLBjvNRVK/PaIiPPQ2Zx2SxMkekQrf8d6ffdYuvndTF4TuZQNYtS1IBXcT8VL9F5p7DR1s5U9YVmMuO/cePbomq7suCR6V7364Oqyz86sfQwTVpeicen0ue99VEXB83rOYwpKHZVN5KW41PY5ezvcoIIPaZ5IsDcy/X6mV2bQeaS4p6fJEUvmkIs5DYS2i6frQZUORIQgZtudv5zOfgoT0BEUQB3h0bh7D8PquIg6F+IyLKLzAe7SKQeM3/CUiPI0xpZvhD7EVZCO1O++2kmhCK+kLa63tFYPZxd/W1mTsv+gjWL030qGcaMlRwOlwsRGu9s7x7HBDNqaJvuvnOX6OlVErCwIn836lHZD/hwoYXXlc1t6UQe2Ei/mRcaizDaNvPPrnvk/3zJHsUne6FjDujv8uPdwYL+wGzavLRwdQBnrbOCAWlTbqwtL3Fa1JFSK5pMrDc+fQlU+bULCXCdqOiA+51COcHjOoUzyGwKyKy4JfDKt+uKQZMBJJucqJiP69955M71+pSYzjJQyZO5UjMPs4lewe5NFkNLiGDunToC03Z8Pw051RaDR9qVsqPcIBiNlu0S0ab0gcDVS10RyHLRuDfCWrxA3y9mOoYb4T+dXiBOjssk85xvIZyP/oPy/vBIwJmXRnNKRAvhJnC30SY0wT583Mc+LSJsejVB2oy7VRr0Ph+6dhDbeDn5BorsEMGe3k4wdzz5o11lUna35V9sHwAGF8nFyJxS0SpNDr+UUeujE0G8V5giOlftzcMptEqv3c2aKyaG3H3wfQIbXkanL1oi7rfOk2WTxbEJRP/H77NcdUZr2qS9/tu6hvefUFx9F7bJc2llydVufISnHbIjDmH+9aX993bW/A0V81c58hke8Skm1CeFGnZ8TqJoTEUmb93F6bPCHD+7CY3P6roSGNBi8NDWOyIsUGOo5npzvtY4kCTbPjn7bp7g+t/OvrwHY7NRGFORqPeYK9p6gpvuze5hrtfeGOAXzLok/K+Lrh5IYxv2xJE4VDah2Kb5QczhQrahABXboI+N8rCmfiyVB31VbGOluty+IbYoVotWMZRCso+6ehEiRpzlEtIPYQJB2LLXrT5aA9ODZ7JGOFqMEDDpIhaEr8zy3k1tPs0dnD0kms3adrFO5t9NxVQ+0u/ZPbj93f96cr//k5vd7r//k5vd7rx9u3kFKKmKpbr0SN2EXptnSpuV5IypD3XJEe8WNWEMGple7P+12gUQddcxP7YLlPUSOErSOJByKt4X874e36yKRoqQItuSSTpKn37YLailGJxpm2ltZtSxI/ZH0UK3z6uupzx2pwimC7ySZhFma1ApaRGeuhk517bJjqD+CAqTc8fANBZOmS4JU2CyKUjLN2iSzlX3bUq+9KXsJe+Ik9OIgU0cVSKE6/dOQ8uaq5S/Hgtt5+K+dh9142HRxmnHX7sYtVpPdruuY5tilyp6lSP+pr0c7iVYp336ek1gkOESsuYojS9yZ7OgphwoegZOr1zEMSuws8KiTt3W46EPHY5s7lLtbHPNQ7pVYvxp26Kzq89Yce98nqOET4TYdAkmW0Xyetfmmsz1kngJO9gEFJ91QdEZLpwQTojBbJvK3gzQ/vg7T7DWcNFPTeZ+tmXb/DYqDNEyPllrZWx0eEcrTp7DCD6RnaOQUY9lffZt07U7wLgjOfs2gbJEWUJPndTo4LwNzDVlNV2vTR0TZ90nIyz2G263Hky1OflF6CbZJeCDpkGLBF68T2yc94phXNbW39a//5KTY/dbRvd5au5Q1Ver6tOPJPlRg2t+SKyW41olsbd3tw5exUubFEbtNavoy8xoxioyo7lzSwSCjIx2kAu37TKT91vd7q8Pt81m7xaACuhGq2C3OS2dRUI+ymXrKoYKHqGym07YznvPHKs9EKMrfyHC4JKnnMCaZhnRm9SAClbzQwdk4So4wzH88S4uQSdLUMbEA3FABa46ESGomVFA9dRzLbXWiQ6xUW17/JEKnOp32cyiQ9o4eduzncH557emNPK/XYUOABatpT2yeg3ZbHjfVHL9IkF9B0isWsfqHJxNNGFfQOaIkqvISaVT4m6mMez+JWD9OIsaPbcXdLzUXLG4fmaAdOblcu1t7Z6q0p0E3ozaomvvSy5zaP+76JzydEu8KVMMnAqv/1lJxfyG1t02G6/s58XeIGu0/rPYUARtHTkvbOFJFpU04yQ2yyD5E7Uc1OhzfStHx0Px0Ifv9tAcFPRVyOpHEewl1K+llnoNzuVL367iy7zPWAh1RKagyiKcDu4tg+BIE6pBn2eRD8JbMqNZtqasm0O6MVpXuXIEStZodmZc8JES13R/b/3hOmt0gbHbnFGCF5xz+hpZUTr82+7wj6wGWjh4O6D6rCwOvF+uKKlFkl7ppONfvLhoZ2M3TGY0mUDcy1Dx707ul/Ry9Mba/DoGO1+nIoxrbq2pLEo1KRxELcZunhlRdFQ5t2fD9gP7XVx1ZKNjmfwEeeojdYP7ZvgAAAGB6VFh0UmF3IHByb2ZpbGUgdHlwZSBpcHRjAAB42j2JwQnAMAwD/56iI9iSaZJ1an/666P7U2NIJRA6Tu7nDTk6DuF0+PJUr/6xtFBw1J0ElcbVC6JNlLmaWYY8BblRVT4x0hTmAhiSJAAAD1RpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+Cjx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IlhNUCBDb3JlIDQuNC4wLUV4aXYyIj4KIDxyZGY6UkRGIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyI+CiAgPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIKICAgIHhtbG5zOmlwdGNFeHQ9Imh0dHA6Ly9pcHRjLm9yZy9zdGQvSXB0YzR4bXBFeHQvMjAwOC0wMi0yOS8iCiAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICB4bWxuczpwbHVzPSJodHRwOi8vbnMudXNlcGx1cy5vcmcvbGRmL3htcC8xLjAvIgogICAgeG1sbnM6R0lNUD0iaHR0cDovL3d3dy5naW1wLm9yZy94bXAvIgogICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICAgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIgogICB4bXBNTTpEb2N1bWVudElEPSJnaW1wOmRvY2lkOmdpbXA6ZGYyMmM2MzEtMTYyMS00NjdkLWE1MTctZTI3MzlkODBhMTNkIgogICB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOmM1Zjc5YTQ4LTFjNDktNDZhNy1iZDZmLWNmYzg4MGMwZWMyYyIKICAgeG1wTU06T3JpZ2luYWxEb2N1bWVudElEPSJ4bXAuZGlkOmJiMjlkMmZkLWRmMTgtNDY1YS05M2JkLTg4MDU1OTU2NDE5NyIKICAgR0lNUDpBUEk9IjIuMCIKICAgR0lNUDpQbGF0Zm9ybT0iV2luZG93cyIKICAgR0lNUDpUaW1lU3RhbXA9IjE1NDgxNjA3NzY2MjEzOTUiCiAgIEdJTVA6VmVyc2lvbj0iMi4xMC40IgogICBkYzpGb3JtYXQ9ImltYWdlL3BuZyIKICAgeG1wOkNyZWF0b3JUb29sPSJHSU1QIDIuMTAiPgogICA8aXB0Y0V4dDpMb2NhdGlvbkNyZWF0ZWQ+CiAgICA8cmRmOkJhZy8+CiAgIDwvaXB0Y0V4dDpMb2NhdGlvbkNyZWF0ZWQ+CiAgIDxpcHRjRXh0OkxvY2F0aW9uU2hvd24+CiAgICA8cmRmOkJhZy8+CiAgIDwvaXB0Y0V4dDpMb2NhdGlvblNob3duPgogICA8aXB0Y0V4dDpBcnR3b3JrT3JPYmplY3Q+CiAgICA8cmRmOkJhZy8+CiAgIDwvaXB0Y0V4dDpBcnR3b3JrT3JPYmplY3Q+CiAgIDxpcHRjRXh0OlJlZ2lzdHJ5SWQ+CiAgICA8cmRmOkJhZy8+CiAgIDwvaXB0Y0V4dDpSZWdpc3RyeUlkPgogICA8eG1wTU06SGlzdG9yeT4KICAgIDxyZGY6U2VxPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDpmOTc3ODE0My0zZDQzLTQ1NmMtYjMxNi1hNmE4OWY1ZDAwZmYiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkdpbXAgMi4xMCAoV2luZG93cykiCiAgICAgIHN0RXZ0OndoZW49IjIwMTktMDEtMjJUMTI6Mzk6MzYiLz4KICAgIDwvcmRmOlNlcT4KICAgPC94bXBNTTpIaXN0b3J5PgogICA8cGx1czpJbWFnZVN1cHBsaWVyPgogICAgPHJkZjpTZXEvPgogICA8L3BsdXM6SW1hZ2VTdXBwbGllcj4KICAgPHBsdXM6SW1hZ2VDcmVhdG9yPgogICAgPHJkZjpTZXEvPgogICA8L3BsdXM6SW1hZ2VDcmVhdG9yPgogICA8cGx1czpDb3B5cmlnaHRPd25lcj4KICAgIDxyZGY6U2VxLz4KICAgPC9wbHVzOkNvcHlyaWdodE93bmVyPgogICA8cGx1czpMaWNlbnNvcj4KICAgIDxyZGY6U2VxLz4KICAgPC9wbHVzOkxpY2Vuc29yPgogIDwvcmRmOkRlc2NyaXB0aW9uPgogPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgIAo8P3hwYWNrZXQgZW5kPSJ3Ij8+2ch2nQAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+MBFgwnJPvKTa8AAA5QSURBVGjezVt7cFRVmv99595+d9JJyDvEJARR3i/lIUQQUKKo4ygMI7LrrGvVWrVTjlu11s6W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"
        self.setWindowIcon(iconFromBase64(self.iconBase64))

    def initBAR(self):
        bar = self.menuBar()
        bar.setStyleSheet("*{color:grey; background-color:qlineargradient(x1:0, y1:1, x0:1, y1:1, stop: 0 rgb(50, 50, 50), stop: 1 rgb(60, 63, 65))}")
        fileMenu = bar.addMenu('File')
        connectAction = QtWidgets.QAction('Connect', self)
        fileMenu.addAction(connectAction)
        #connectAction.triggered.connect(self.makeConnection)
        configAction = QtWidgets.QAction('Config', self)
        fileMenu.addAction(configAction)
        configAction.triggered.connect(lambda: self.configMenu.show())
        exitAction = QtWidgets.QAction('Exit', self)
        fileMenu.addAction(exitAction)
        exitAction.triggered.connect(self.exit)

    def initIcon(self):
        self.sysTray = QtWidgets.QSystemTrayIcon(self)
        self.iconBase64 = b"iVBORw0KGgoAAAANSUhEUgAAAEAAAAA+CAYAAACbQR1vAAAZw3pUWHRSYXcgcHJvZmlsZSB0eXBlIGV4aWYAAHjarZtrduS4joT/axWzBPFNLofPc2YHs/z5glTa6bKrqnvu2N3OdFoSSSAQCICsa/7Pf6/rv/hKLsXLh5RjifHmyxdfbOVNvs/XeTW33z/3l3/+xO9fPr/cfP5g+cjx6s6v8fncVD4Pnzek50mmff38Sv15Tn4eZD4evL+cRtb757r8PMjZ87l5fr/Kc1/1b8t5/rf9eezz8F9/9wljjMDznL3sdMbd/PQaxTEDV1zdr5XfrdU7y3u3P3cu/my76+PtL8Zb+Wfb3fW5wn01xXXH54L4i42ez0345XP34TX7ZUbm9dZ+/UMr+OX96812a4281jyrqz5iqXg9i3qZcL/jQh7i3b4t8p34P/A+7e/Cd2aJHY8NvNn47pcpxmLtZbwZpppl5n7tpjNFb6dNvFrbrdufZZdssX07w+vbLJtww7hcxicdrzk+th9zMXvcssfrJjPyMFxpDQ+TF799Xz99+H/5/njQWoKuMduYeduKeVlhmmnIc/rJVTjErMemYdt3f18fbv38kmMdHgzbzJkF1rudR7RgPrHltp8d14XbX084mzSeB2Aixg5Mxjg8cEfjgonmTtYmY7Bjxj+VmVvnbcMDJgQ7zLXwDbjHOdlqbO5JZl9rgz0fQy04IrjoEq4hUHCW9wH8JJ/BUA0u+CuEEEMKOZRQo4s+hhhjiuKoCmH5FFJMKeVUUs0u+xxyzCnnXHIttjgoLJRY0lVyKaVWBq08unJ35Ypam22u+RZabKnlVlrtwKf7Hnrsqedeeh12uEH4jzjSNfIoo04zgdL0M8w408yzzLrA2nLLr7DiSiuvsuqH1x6vfvWa+cVzf/aaebwmj/l9Xfr0Gh+n9HqEEZ0E+QyPWW/weJIHALSVz+5svLfynHx2F0tQBIvXTJBzhpHH8KCfxoZlPnz36bk/+u0K/l/5zf7Oc5dc9//huUuuezz33W8/eG3UnVHcdpCiUDa93YLYPH+MbU2WtBZDL0JyYJGJ9ebSb82PtDqjr/3I/UlsXSnsrjZXvV6vN++vq8Y0TZ/Z6Ka7dgbwbQ2b9mvzrlf9pXCZXyWxinWtFPtMXJE8xrFjYgLeuFYWXk3Nhg7BxNXcHLoZ45HpZ9f73vJ0zLKGVC87ethPHy0tfNcj5tjLqyMEU1qKLtdB3kut9IapV3Sd50zjZ1rDyxbWMyOt2FX+WlxonRHGXtA6P2cLERoJuDQZn1hTwx+tRFNncqubVXmW9eVqy/TozFwB0g+p15xnjMQAayg1DBJPSWblAf7gJW9676LvEGD9lCaPKxryiq9l9LbybN0dA5dO7mJ2zk2WHh0GWzMAudJWwlrgvsexRmxhMmS6L0ybRyg83acyu1vAoY+xDUuWnefBLEcJxrYyFoBe99SnUyw++772yqWm0docbcbjibZKaC5GDBpLc9w6x7BtEG4xtDzwZ0krVIYzgTQ1cUYal3AQBZ179dimYeTsgThzmywj2tXMKpjB9oZ1Fh+txrJclCNmSBMb3S5di4SXVrw3Rkpm/gAmTUDQ202MMLMB7IcR2tIsAKTe5N/gbQUqMEkOBjdcsFfWGx+kvr6+nnCZw22kOQvSRhvnM1PloxMwCrHrxxiD7PYw76+JqRJt9557s6uzXPmL5TqXtLSW4xCUtnfGDcKSR6IyIpciJfD+PH9jOByTAMoqEfuw6tLaGPLIdVwC8ICHw4jMPwfbAJoNofvQfMYbKz6LBAZztjgHPjUxwUWVmRLvV6vwciOeZoBTE+y8DeSQNKKDKr37l9cy82oX4ROTA5Y2t3tOWJiI7nYdfIv0Hny7d3y3B9/hAwcXczasxChl2dYBKpPOBP2ClkHqwa1WZ5ugULCFY2joqYk+iJIy8qxXWTFoIP4kxoBCDCE3RwCWxc6ckAidzI8yngHaa6Bqj3EYDjYxhCWZtsitA0IIBcjBfBiWJHvDErF2/o+ltnoIFAH3MowA9MbQxNoG0BtFc80bRaOSdct3iiamUIyE7H14k0zLmnnu5hTw0jaLluheKNG4H1xcubGvO68nsA6+dBcioq4PgM3XrY5lTsi+iX+ABFRbwFCFQOsKrXofh2ASyAcSZQAG93OxiMHklSoGA+ZJMTGVMH0hUJOCnUetQkSIwDtsfovGhjUwh4cyy1XDHNZx88KXOBJ2LijlGDNsZOY0//Dz63d/mDgP/JMkcHWYFcgzeM5eSDKgpxIJ6I9IukYR1CtPqwjuCt6e2kBbwEvTAEHMVETtoO5WjljZ4BbD+3bjVt8BNzBsG+9XkMoQsx5n5ylkLg+eCMcQmxPxEhd4zozZbC1oJ9RMMJj+XgH3FmDacL+Bz40gCjieodrbUO8jfY4DGVM/1WZmthuy1wMxU/4CxsOM2PNk/T3Nce6JeaR8qVI2QpA+IuudoPWZ/O1gbpARCW+7k2gUkQ6WuG6l7M0QHfoW8nbKNiwBpiepPioDIMOeQFKpSFVvU/4hDMsM4kkBC2S1UNPdGppghWtqaQ2l2ebqyp9wGmtFnC2HdOystaIwyQS5Tuk6LMVE8ZzkCvk7wZTO5Kvv6cIpPeWGPzX4QMZuMu0tSHfwYlP2diwppQhampSNPIJmSL6B8gvmJ3ut1GZbXUJPlUJAsj42KIkQzdgkVJgMUbOzCEMwlY6PK9pxpF4uch1ZpUvoKJFP5AzjxId4up/t/knUvb06aHUlEiR2jiK5uIaesR20skAOa1AROn5FBYJ7yPtkkw73ET4O8tuzbrLRIQnWtGXKXNtv915WgHOr1tLRaySivD9N5CeYx3rKgQ5EuugdxYZY2Tm2TEE2MSvcjapwUzcBTp+WzLpnAnMgv+OYopA8b1iMIM9KR8tpKR4h69EwFfbaEoQsoUyhnHMWW6SM60LbtIlOB8DclKHJaRiy2esJY6Ut3KtxJe7H0S9bUUvEdB7ZqDL4bwWKCsoynOhBwmw7oabLGRD0L1THD6KDt/e40s6NihlJK/LS1knKjzwtKz9JiT0Rs14R4wYAum0cVhVPxQ9w9jxCGN2BHcp5UFlbDuqBii7YAAO6L0kWigy19UKYjNIjS1MZFEa7qWwMdwWVTXU+iOT2W7HmosLuNvOWcSQY+GBZ2K7LepTrxFAELngBi+7qgEoJeI9JjLpwD4IGZiNGO3wx7SLTBG8YPPf3cLk+48UamHoElCIki/OzAhyRjdCqkH8/JLb5pEASwxYfa2uVAK0dWWMoPhMVYfNLLumFoi+/3+be3lPL+WIGgIx4++PSrfxf14pa9/tCQfz9wr9dd/3TC79ch7wDZxYFjoBSjVTrFWvpaDfUUPMoLmhL+cNLc6oY43okAIqulTm2Tk0KIxiyg6t+WDhDZpfCLxBqFI2Q/NwINqfSaIEcG2xG9BtLsYjQhAsrEKKAf0q/jErcsX19BPcObUQjieloaQW1CoHDDfjHVTQetT+pSGqsQR7txHzwSL8ugLVAsZyYVqYeIhpMCMWsI0QsZOXUSEVzqFiisP5IRaRvwU5e26lIOty9ZGd6ZGd7RcTOrJs+yJ7oVrG15Ycm25VQGyno6qa1E09T1GG+hCX5AgUcLFZBIXliZZJW+09ccL3IgFswaVGJQS1wZAhD7lsIFoC8Ds98sow4plBztnlbqDb7+0UfBqo/5UZcp8rSGnfVT4DjysjqJnantApVAmhki9ovu8wikZb4WWDNUONwJSrN+OXHkA29aiCE/u4VoMWTRCb0DhDJGmI0qHYTKgKQ4nv5g14EJ3KFjAi9kQ7qLuFVTuli0K7MP3uiMo6WRE8GSBib2+8hTmAx8UnQd6TKh4wT+QIhnbellloYajNM0Kl6oTnxi1h+KouIgSQ6bobY9Xfbs8rh3gweqOrWlMyBsIi4YKwLGUihICw4X5olF5NFkG87s52rCctepd88oBt+a3C7yZgESDVNFkf1Y24mqMpEcNO117eL8zOfdObDGB/zcXqMU1+J2cTP2Wgy1z+eDTK6mfunyejv/uo7P+3rz3SeEb4P8NN0Pud+fZ18Tcp2Nin/nKYGHlIXRY2WKjmiLhNP9BOduawZqi3xFhUkiS8Jv2nd6ryg4Bb6GvrPsEXcdejpx9So/gg6LMHuKjX9LhihiETFcAEBKUeuwPNJHcgtJglrIjifBwxtOyAPUyuZQQbiQD1ymGergygRfTnlXGrcREwQy1atroedyUId/flZNiZ7FE0yH1yFejxEB2fHm6yWCZkgVU3ypHTfrid/hS1iMlJbZL/LaTvmlk67uXDYcxt7bWaL4tS+a0fzFIDpvQBEhVmSJHImehJtUlvwK6lcm1WgBtQfKkliDWbaEf9T77GagktEFOqZmbi8z1mNiHwpw+fPrsMXhT5nRsMRoG1TQNqrD8o/8MAuwAyU1wyeu/GahZjByJxKdRRD071MnXjoCE5hLj5CZJQZn95AFxOgNMRHKGxqkcNHm2X0HG5fdcsNRwUFg9iWXwzahCTYHOAE8lk/+Cqo3DWuN01bqcKACm5K8VvH4HtrBQlLclYzQeR7YZGwhfLguWmgpovkYXbymBObkhjDusMGP8L1A+dMchS4G9zGalgaSsBgoXZEImkvnF7cLnZAqeJTDdO7vZCu3oU0E8LCIhXUsKPKrus3mN6S7CfJXkbM8ddFX5/A7xA8iV0OUjd0txTwmALV1YmQl9iWmpz8PSl5q1YgPVAlV6SfjSL3TKJNv61YETxgxIT+ez1+mTq6Cc67WiqlQ70fJe9N9z9nO2LJmniK+10GLpWB15c6kDjZTb2nSIKLKFwxiw9WUrZZN6nGc9qocsaqngynkX2BrvCBroMtQesrsPzfgXXxxnm1R2+VcSPGGwvD76VFKSX8WIMjDbkkkfeqWMWUhMBTxTjo5FLT4BQOzSLX5F6KSiTlDduibpr9BQO/UXbXV2kHR8Rvndtd/5hY/abctXsJyLHZS0Ah8FdUnN/6aEZzIn584gJYUBwR2da1+pudE9I847OMGduFF7507z6ad+P2WTVprmZAciY1a8oDjfIdGtcbNvAqTCJkFPUkUVb5ExgVLUnxRs0CMMxp0mZwnpBCqMV1uY+Y5y51v0V8Er9QUNYzd0+wkO9A1cm+FPKHrvyB1AbU9U5X4Rtd/XO2un5F11dQJWV67YzsLbbUk0A1XbDSwK9lqt3RLtt6NHCSmpnmSd9DLQOpxHjy9638nU7+3kqgnsAQKl+kdMFKSLCTgxU/ZvdjTvx8T8LSJYcTDmV5Zx7cESJv/VeoNTdLHbz3MNQEnsdGqKH7IaRe1VSAkLDzJiQeDvSug71NScOMun5X/c8SyWqKN96Du01dn8Qlr8FcfuB5hK+KjJQ+ivaoyh+23EV7W6evnkT5InWQGwiCTGyR9y7ftY1Dmq6nIwa99j/k3X6WsnbmVftO2AW48Zq7f+LQGTv1wsROxq73bqwgKvbiJI+cNLw9Bj8qHmgUlRlbjdxqliU3yWH2CHmUlj++YeDRRA8UVfKmOxl4i9Bu9ibVeoH22qgliEp0PIKqTo0cs5WOcpxXI5/Kv5x0ZEVRUvhynPbgtugZ2l6dQuEWuIeZyv6JDWYrFcVK4Te1ST0MVawOK+2y76TSWg7iEBGHIcPedmzSLTXskXs5O5DUfYSIthSKcUw+1y0sc1C+I1COhD6KTcZrW6ZramdimtYmr5mxF0rF2kRYw5Xud0NequSfuZ6Zap4KEKbJXNQb99BUVUy+RvvJENfPE33Ns5ictA0l+8T49qxfZ17V84cd1OTVJl9wKR/BtdrbvCDbLGWKco2oyqE9xYCES1vCkVlcv9Sw3Q09JHXqVGuE64Ly9uDStpobFVogt0F14BMNTfhSZojihordRP69CDsQlREJutNGd0jVHBFTG4Kg9trT3RUrLf9O2F9/UEGBguF7g3bebTKy+qFO/PD0AC5EeDamxqX+dQ+7VyyryR3aws2aZxjaXGtWpYEAONZrp3VnaKxDplVjLJAviZGabjgpTlVAv+WlqP3Jvjdgo8oNLG6Ivmtqu83/4ZzBchM66/5wVEjaWzrNISsRpD6jmpWX2irlaasc+7TPVqMxyh7kDVFPJu8rEdUeht97oks71J0kWKlpRy1IeouIcO3ZlFU+/qUhMYcXjbTfFwCXKoAgMiNE7MduLaauI7AwYCF+/pR4nwqv1By1ayaFB0MqT03Vq08i7gAThjmd16wjB6qf9uPb2VtcCkkSYBM9b5Ri60GChM4NZhqumhDwlWmjKZFSnxQCpNkQrBqyXF73XhFTb7NCP9KQqlxIr+HQyFLPip+hVNWqBOWeQyZwCSwChj+quXzjlgWbLBjvNRVK/PaIiPPQ2Zx2SxMkekQrf8d6ffdYuvndTF4TuZQNYtS1IBXcT8VL9F5p7DR1s5U9YVmMuO/cePbomq7suCR6V7364Oqyz86sfQwTVpeicen0ue99VEXB83rOYwpKHZVN5KW41PY5ezvcoIIPaZ5IsDcy/X6mV2bQeaS4p6fJEUvmkIs5DYS2i6frQZUORIQgZtudv5zOfgoT0BEUQB3h0bh7D8PquIg6F+IyLKLzAe7SKQeM3/CUiPI0xpZvhD7EVZCO1O++2kmhCK+kLa63tFYPZxd/W1mTsv+gjWL030qGcaMlRwOlwsRGu9s7x7HBDNqaJvuvnOX6OlVErCwIn836lHZD/hwoYXXlc1t6UQe2Ei/mRcaizDaNvPPrnvk/3zJHsUne6FjDujv8uPdwYL+wGzavLRwdQBnrbOCAWlTbqwtL3Fa1JFSK5pMrDc+fQlU+bULCXCdqOiA+51COcHjOoUzyGwKyKy4JfDKt+uKQZMBJJucqJiP69955M71+pSYzjJQyZO5UjMPs4lewe5NFkNLiGDunToC03Z8Pw051RaDR9qVsqPcIBiNlu0S0ab0gcDVS10RyHLRuDfCWrxA3y9mOoYb4T+dXiBOjssk85xvIZyP/oPy/vBIwJmXRnNKRAvhJnC30SY0wT583Mc+LSJsejVB2oy7VRr0Ph+6dhDbeDn5BorsEMGe3k4wdzz5o11lUna35V9sHwAGF8nFyJxS0SpNDr+UUeujE0G8V5giOlftzcMptEqv3c2aKyaG3H3wfQIbXkanL1oi7rfOk2WTxbEJRP/H77NcdUZr2qS9/tu6hvefUFx9F7bJc2llydVufISnHbIjDmH+9aX993bW/A0V81c58hke8Skm1CeFGnZ8TqJoTEUmb93F6bPCHD+7CY3P6roSGNBi8NDWOyIsUGOo5npzvtY4kCTbPjn7bp7g+t/OvrwHY7NRGFORqPeYK9p6gpvuze5hrtfeGOAXzLok/K+Lrh5IYxv2xJE4VDah2Kb5QczhQrahABXboI+N8rCmfiyVB31VbGOluty+IbYoVotWMZRCso+6ehEiRpzlEtIPYQJB2LLXrT5aA9ODZ7JGOFqMEDDpIhaEr8zy3k1tPs0dnD0kms3adrFO5t9NxVQ+0u/ZPbj93f96cr//k5vd7r//k5vd7rx9u3kFKKmKpbr0SN2EXptnSpuV5IypD3XJEe8WNWEMGple7P+12gUQddcxP7YLlPUSOErSOJByKt4X874e36yKRoqQItuSSTpKn37YLailGJxpm2ltZtSxI/ZH0UK3z6uupzx2pwimC7ySZhFma1ApaRGeuhk517bJjqD+CAqTc8fANBZOmS4JU2CyKUjLN2iSzlX3bUq+9KXsJe+Ik9OIgU0cVSKE6/dOQ8uaq5S/Hgtt5+K+dh9142HRxmnHX7sYtVpPdruuY5tilyp6lSP+pr0c7iVYp336ek1gkOESsuYojS9yZ7OgphwoegZOr1zEMSuws8KiTt3W46EPHY5s7lLtbHPNQ7pVYvxp26Kzq89Yce98nqOET4TYdAkmW0Xyetfmmsz1kngJO9gEFJ91QdEZLpwQTojBbJvK3gzQ/vg7T7DWcNFPTeZ+tmXb/DYqDNEyPllrZWx0eEcrTp7DCD6RnaOQUY9lffZt07U7wLgjOfs2gbJEWUJPndTo4LwNzDVlNV2vTR0TZ90nIyz2G263Hky1OflF6CbZJeCDpkGLBF68T2yc94phXNbW39a//5KTY/dbRvd5au5Q1Ver6tOPJPlRg2t+SKyW41olsbd3tw5exUubFEbtNavoy8xoxioyo7lzSwSCjIx2kAu37TKT91vd7q8Pt81m7xaACuhGq2C3OS2dRUI+ymXrKoYKHqGym07YznvPHKs9EKMrfyHC4JKnnMCaZhnRm9SAClbzQwdk4So4wzH88S4uQSdLUMbEA3FABa46ESGomVFA9dRzLbXWiQ6xUW17/JEKnOp32cyiQ9o4eduzncH557emNPK/XYUOABatpT2yeg3ZbHjfVHL9IkF9B0isWsfqHJxNNGFfQOaIkqvISaVT4m6mMez+JWD9OIsaPbcXdLzUXLG4fmaAdOblcu1t7Z6q0p0E3ozaomvvSy5zaP+76JzydEu8KVMMnAqv/1lJxfyG1t02G6/s58XeIGu0/rPYUARtHTkvbOFJFpU04yQ2yyD5E7Uc1OhzfStHx0Px0Ifv9tAcFPRVyOpHEewl1K+llnoNzuVL367iy7zPWAh1RKagyiKcDu4tg+BIE6pBn2eRD8JbMqNZtqasm0O6MVpXuXIEStZodmZc8JES13R/b/3hOmt0gbHbnFGCF5xz+hpZUTr82+7wj6wGWjh4O6D6rCwOvF+uKKlFkl7ppONfvLhoZ2M3TGY0mUDcy1Dx707ul/Ry9Mba/DoGO1+nIoxrbq2pLEo1KRxELcZunhlRdFQ5t2fD9gP7XVx1ZKNjmfwEeeojdYP7ZvgAAAGB6VFh0UmF3IHByb2ZpbGUgdHlwZSBpcHRjAAB42j2JwQnAMAwD/56iI9iSaZJ1an/666P7U2NIJRA6Tu7nDTk6DuF0+PJUr/6xtFBw1J0ElcbVC6JNlLmaWYY8BblRVT4x0hTmAhiSJAAAD1RpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+Cjx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IlhNUCBDb3JlIDQuNC4wLUV4aXYyIj4KIDxyZGY6UkRGIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyI+CiAgPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIKICAgIHhtbG5zOmlwdGNFeHQ9Imh0dHA6Ly9pcHRjLm9yZy9zdGQvSXB0YzR4bXBFeHQvMjAwOC0wMi0yOS8iCiAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICB4bWxuczpwbHVzPSJodHRwOi8vbnMudXNlcGx1cy5vcmcvbGRmL3htcC8xLjAvIgogICAgeG1sbnM6R0lNUD0iaHR0cDovL3d3dy5naW1wLm9yZy94bXAvIgogICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICAgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIgogICB4bXBNTTpEb2N1bWVudElEPSJnaW1wOmRvY2lkOmdpbXA6ZGYyMmM2MzEtMTYyMS00NjdkLWE1MTctZTI3MzlkODBhMTNkIgogICB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOmM1Zjc5YTQ4LTFjNDktNDZhNy1iZDZmLWNmYzg4MGMwZWMyYyIKICAgeG1wTU06T3JpZ2luYWxEb2N1bWVudElEPSJ4bXAuZGlkOmJiMjlkMmZkLWRmMTgtNDY1YS05M2JkLTg4MDU1OTU2NDE5NyIKICAgR0lNUDpBUEk9IjIuMCIKICAgR0lNUDpQbGF0Zm9ybT0iV2luZG93cyIKICAgR0lNUDpUaW1lU3RhbXA9IjE1NDgxNjA3NzY2MjEzOTUiCiAgIEdJTVA6VmVyc2lvbj0iMi4xMC40IgogICBkYzpGb3JtYXQ9ImltYWdlL3BuZyIKICAgeG1wOkNyZWF0b3JUb29sPSJHSU1QIDIuMTAiPgogICA8aXB0Y0V4dDpMb2NhdGlvbkNyZWF0ZWQ+CiAgICA8cmRmOkJhZy8+CiAgIDwvaXB0Y0V4dDpMb2NhdGlvbkNyZWF0ZWQ+CiAgIDxpcHRjRXh0OkxvY2F0aW9uU2hvd24+CiAgICA8cmRmOkJhZy8+CiAgIDwvaXB0Y0V4dDpMb2NhdGlvblNob3duPgogICA8aXB0Y0V4dDpBcnR3b3JrT3JPYmplY3Q+CiAgICA8cmRmOkJhZy8+CiAgIDwvaXB0Y0V4dDpBcnR3b3JrT3JPYmplY3Q+CiAgIDxpcHRjRXh0OlJlZ2lzdHJ5SWQ+CiAgICA8cmRmOkJhZy8+CiAgIDwvaXB0Y0V4dDpSZWdpc3RyeUlkPgogICA8eG1wTU06SGlzdG9yeT4KICAgIDxyZGY6U2VxPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDpmOTc3ODE0My0zZDQzLTQ1NmMtYjMxNi1hNmE4OWY1ZDAwZmYiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkdpbXAgMi4xMCAoV2luZG93cykiCiAgICAgIHN0RXZ0OndoZW49IjIwMTktMDEtMjJUMTI6Mzk6MzYiLz4KICAgIDwvcmRmOlNlcT4KICAgPC94bXBNTTpIaXN0b3J5PgogICA8cGx1czpJbWFnZVN1cHBsaWVyPgogICAgPHJkZjpTZXEvPgogICA8L3BsdXM6SW1hZ2VTdXBwbGllcj4KICAgPHBsdXM6SW1hZ2VDcmVhdG9yPgogICAgPHJkZjpTZXEvPgogICA8L3BsdXM6SW1hZ2VDcmVhdG9yPgogICA8cGx1czpDb3B5cmlnaHRPd25lcj4KICAgIDxyZGY6U2VxLz4KICAgPC9wbHVzOkNvcHlyaWdodE93bmVyPgogICA8cGx1czpMaWNlbnNvcj4KICAgIDxyZGY6U2VxLz4KICAgPC9wbHVzOkxpY2Vuc29yPgogIDwvcmRmOkRlc2NyaXB0aW9uPgogPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgIAo8P3hwYWNrZXQgZW5kPSJ3Ij8+2ch2nQAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+MBFgwnJPvKTa8AAA5QSURBVGjezVt7cFRVmv99595+d9JJyDvEJARR3i/lIUQQUKKo4ygMI7LrrGvVWrVTjlu11s6W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"
        self.sysTray.setIcon(iconFromBase64(self.iconBase64))
        self.sysTrayMenu = QtWidgets.QMenu(self)
        showAction = self.sysTrayMenu.addAction("Show")
        showAction.triggered.connect(self.mainPopUp)
        self.sysTray.setContextMenu(self.sysTrayMenu)
        self.sysTray.activated.connect(self.onTrayIconActivated)
        self.sysTray.show()
        self.sysTray.setVisible(False)

    def initConfigMenu(self):
        self.configMenu = Config((self.geometry().left(), self.geometry().left()))

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
        #print (self.socket)
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

    def removeTemps(self):
        if os.path.exists(tempDir):
            for i in os.listdir(tempDir):
                try:
                    shutil.rmtree(os.path.join(tempDir, i))
                except Exception:
                    pass

    def makeConnection(self):
        try:
            #print('trying to connect')
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((serverIP, serverPort))
            self.connected = True

        except Exception:
            print('Couldn\'t connect')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("fusion")
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    lockFile = QLockFile(tempfile.gettempdir() + "/AniStreamer.lock")
    if lockFile.tryLock(100) != True:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle('WARNING')
        msg.setText("You already have this app running.")
        msg.exec()
        app.quit()
        sys.exit()
    else:
        ex = Client()
        sys.exit(app.exec_())