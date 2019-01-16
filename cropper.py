from main import *
from jobhandler import *
from PyQt5.QtWidgets import QLabel, QMainWindow, QApplication, QWidget, QVBoxLayout, QScrollArea, QSlider
from PyQt5.QtGui import QPixmap, QMouseEvent, QImage
import os, time
from PyQt5 import QtCore

class MyLabel(QLabel):
    def __init__(self):
        QLabel.__init__(self)

    def mouseMoveEvent(self, event: QMouseEvent):
        print(event.pos())

class Cropper(QMainWindow):
    def __init__(self, job):
        QMainWindow.__init__(self)
        self.targaLabel = 'TRUEVISION-XFILE  '
        self.job = job
        self.sl = None
        self.setWindowTitle("CROP AREA")
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.setStyleSheet("background-color: rgb(50, 50, 50);")
        #self.setMaximumSize(1920,1080)
        #self.setGeometry(0,0,int(job.resolution.split('x')[0]),int(job.resolution.split('x')[1]))
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.lay = QVBoxLayout(self.centralWidget)
        self.lay.setAlignment(Qt.AlignTop)
        self.scrollArea = QScrollArea()
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("background-color: rgb(60, 63, 65);")
        self.scrollArea.setObjectName("PREVIEW")
        self.scrollArea.setEnabled(True)
        self.lay.addWidget(self.scrollArea)
        self.label = MyLabel()
        self.scrollArea.setWidget(self.label)

        if self.job.type == 'Still':
            print(self.job.isTGA)
            imageData = open(job.path, 'rb')
            if self.job.isTGA:
                barray = QtCore.QByteArray()
                barray.append(imageData.read())
                for i in self.targaLabel:
                    barray.append(i)
                qdata = QImage.fromData(barray, 'tga')
            else:
                barray = QtCore.QByteArray()
                barray.append(imageData.read())
                qdata = QImage.fromData(barray)

            pixmap = QPixmap.fromImage(qdata)
            self.label.setPixmap(pixmap)

        elif self.job.type == 'Sequence':
            imageData = open(os.path.join(self.job.path, self.job.content[0]), 'rb')
            if self.job.isTGA:
                barray = QtCore.QByteArray()
                barray.append(imageData.read())
                for i in self.targaLabel:
                    barray.append(i)
                qdata = QImage.fromData(barray, 'tga')
            else:
                barray = QtCore.QByteArray()
                barray.append(imageData.read())
                qdata = QImage.fromData(barray)

            pixmap = QPixmap.fromImage(qdata)
            self.label.setPixmap(pixmap)

            self.sl = QSlider(Qt.Horizontal)
            self.sl.setMaximum(len(self.job.content) - 1)
            self.sl.setValue(0)
            self.sl.setTickPosition(QSlider.TicksBelow)

            if self.job.fps:
                self.sl.setTickInterval(job.fps)
            else:
                self.sl.setTickInterval(25)

            self.lay.addWidget(self.sl)
            self.sl.valueChanged.connect(self.valuechange)

        if self.label.sizeHint().width() >= 1902:
            self.scrollArea.setMinimumWidth(1902)
            self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        else:
            self.scrollArea.setMinimumWidth(self.label.sizeHint().width())

        if self.label.sizeHint().height() >= 980:
            self.scrollArea.setMinimumHeight(980)
            self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        else:
            self.scrollArea.setMinimumHeight(self.label.sizeHint().height())

        if self.sl:
            self.sl.setMaximumWidth(self.lay.sizeHint().width()/2)
            self.sl.setMinimumWidth(50)

        self.setFixedSize(self.lay.sizeHint())
        self.show()

        print('scrollbox', self.scrollArea.frameGeometry())
        print('image', pixmap.width(), pixmap.height())
        #print('slider', self.sl.frameGeometry())
        print('window', self.geometry())
        print('layout', self.lay.sizeHint())

    def valuechange(self):
        position = self.sl.value()
        try:
            imageData = open(os.path.join(self.job.path, self.job.content[position]), 'rb')
            if self.job.isTGA:
                barray = QtCore.QByteArray()
                barray.append(imageData.read())
                for i in self.targaLabel:
                    barray.append(i)

                qdata = QImage.fromData(barray, 'tga')
            else:
                barray = QtCore.QByteArray()
                barray.append(imageData.read())
                qdata = QImage.fromData(barray)

            pixmap = QPixmap.fromImage(qdata)
            self.label.setPixmap(pixmap)
        except Exception:
            print('something went wrong')

