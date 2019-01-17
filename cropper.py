from main import *
from jobhandler import *
from PyQt5.QtWidgets import QLabel, QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QSlider, QSpacerItem, QLineEdit
from PyQt5.QtGui import QPixmap, QMouseEvent, QImage
import os, time
from PyQt5 import QtCore

class MyLabel(QLabel):
    def __init__(self):
        QLabel.__init__(self)
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.crop = QLabel(self)
        self.crop.setGeometry(0,0, 100, 100)
        self.crop.setStyleSheet("background-color: rgb(50, 50, 50)")
        self.cropp = (10000, 10000)

    def paintEvent(self, event):
        super(MyLabel, self).paintEvent(event)
        qp = QtGui.QPainter(self)
        br = QtGui.QBrush(QtGui.QColor(100, 10, 10, 40))
        qp.setBrush(br)
        qp.drawRect(QtCore.QRect(self.begin, self.end))

    def getPos(self, event):
        pos = [0, 0]
        if event.pos().x() < 0:
            pos[0] = 0
        elif event.pos().x() > self.geometry().width():
            pos[0] = self.geometry().width()
        else:
            pos[0] = event.pos().x()

        if event.pos().y() < 0:
            pos[1] = 0
        elif event.pos().y() > self.geometry().height():
            pos[1] = self.geometry().height()
        else:
            pos[1] = event.pos().y()

        return pos

    def mousePressEvent(self, event: QMouseEvent):
        self.begin = event.pos()
        self.end = event.pos()
        #self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        #self.update()

class Cropper(QMainWindow):
    def __init__(self, job):
        QMainWindow.__init__(self)
        self.targaLabel = 'TRUEVISION-XFILE. '
        self.job = job
        self.sl = None
        self.setWindowTitle("EDIT")
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.setStyleSheet("background-color: rgb(50, 50, 50);")
        #self.setMaximumSize(1920,1080)
        #self.setGeometry(0,0,int(job.resolution.split('x')[0]),int(job.resolution.split('x')[1]))
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.lay = QVBoxLayout(self.centralWidget)
        self.lay.setAlignment(Qt.AlignTop)
        self.layTop = QVBoxLayout(self.centralWidget)
        self.layTop.setAlignment(Qt.AlignHCenter)
        self.layBottom = QHBoxLayout(self.centralWidget)
        self.layBottom.setAlignment(Qt.AlignHCenter)
        self.scrollArea = QScrollArea()
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("background-color: rgb(60, 63, 65);")
        self.scrollArea.setObjectName("PREVIEW")
        self.scrollArea.setEnabled(True)
        self.label = MyLabel()
        self.scrollArea.setWidget(self.label)
        self.layTop.addWidget(self.scrollArea)
        self.lay.addLayout(self.layTop)
        self.lay.addLayout(self.layBottom)

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

            self.layBottom.addWidget(self.sl)
            self.sl.valueChanged.connect(self.valuechange)
            self.sl.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        self.vertSpacer = QSpacerItem(20, 0)

        font = QtGui.QFont('SansSerif', 12)
        self.layBottom.addItem(self.vertSpacer)
        self.coordinateLabels =  [QLabel(x) for x in ["<font color='grey'>X:</font>", "<font color='grey'>Y:</font>", "<font color='grey'>W:</font>", "<font color='grey'>H:</font>"]]
        self.coordinateEntry = [QLineEdit(x) for x in ['0', '0', '0', '0']]
        [x.setFont(font) for x in self.coordinateLabels]
        for i in range(4):
            self.layBottom.addWidget(self.coordinateLabels[i])
            self.layBottom.addWidget(self.coordinateEntry[i])
            self.coordinateEntry[i].setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        [x.setFixedSize(x.sizeHint()) for x in self.coordinateLabels]
        [x.setFixedWidth(34) for x in self.coordinateEntry]
        [x.setStyleSheet("color: 'grey'; background-color: rgb(60, 63, 65)") for x in self.coordinateEntry]

        if self.label.sizeHint().width() >= 1902:
            self.scrollArea.setFixedWidth(1902)
            self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            self.layTop.activate()
            self.setFixedWidth(self.lay.sizeHint().width())
        else:
            self.scrollArea.setFixedWidth(self.label.sizeHint().width())
            if self.label.sizeHint().width() <= 302:
                self.setFixedWidth(320)
            else:
                self.layTop.activate()
                self.setFixedWidth(self.lay.sizeHint().width())

        if self.label.sizeHint().height() >= 980:
            self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            self.scrollArea.setFixedHeight(980)
            self.layTop.activate()
            self.setFixedHeight(self.lay.sizeHint().height())
        else:
            self.scrollArea.setFixedHeight(self.label.sizeHint().height())
            self.layTop.activate()
            self.setFixedHeight(self.lay.sizeHint().height())

        if self.sl:
            self.sl.setFixedWidth(self.geometry().width()/2)

        #self.setFixedSize(self.lay.sizeHint())
        print('mainlayout', self.label.cropp)

        self.show()
        print('mainlayout', self.lay.sizeHint())
        print('toplayout', self.layTop.sizeHint())
        print('bottomlayout', self.layBottom.sizeHint())
        print('scrollbox', self.scrollArea.frameGeometry())
        print('image', pixmap.width(), pixmap.height())
        print('label', self.label.sizeHint())
        print('window', self.geometry())

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

