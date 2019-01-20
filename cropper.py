from main import *
from jobhandler import *
from PyQt5.QtWidgets import QLabel, QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QSlider, QSpacerItem, QLineEdit, QPushButton, QToolTip
from PyQt5.QtGui import QPixmap, QMouseEvent, QImage, QIntValidator
import os, time
from PyQt5 import QtCore

class MyLabel(QLabel):
    coordSignal = QtCore.pyqtSignal(int, int, int, int)
    def __init__(self):
        QLabel.__init__(self)
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.crop = QLabel(self)
        self.crop.setStyleSheet("background-color: rgba(100, 0, 0, 40);border: 1px inset black")

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
        self.crop.show()
        self.crop.setGeometry(0,0,0,0)
        self.cropSize = [0,0,0,0]
        self.myPosStart = self.getPos(event)

    def mouseMoveEvent(self, event):
        self.myPosEnd = self.getPos(event)
        if self.myPosEnd[0] > self.myPosStart[0]:
            self.crop.x = self.myPosStart[0]
            self.crop.w = self.myPosEnd[0] - self.myPosStart[0]
        else:
            self.crop.x = self.myPosEnd[0]
            self.crop.w = self.myPosStart[0] - self.myPosEnd[0]

        if self.myPosEnd[1] > self.myPosStart[1]:
            self.crop.y = self.myPosStart[1]
            self.crop.h = self.myPosEnd[1] - self.myPosStart[1]
        else:
            self.crop.y = self.myPosEnd[1]
            self.crop.h = self.myPosStart[1] - self.myPosEnd[1]

        self.crop.setGeometry(self.crop.x, self.crop.y, self.crop.w, self.crop.h)
        self.coordSignal.emit(self.crop.x, self.crop.y, self.crop.w, self.crop.h)

    def mouseReleaseEvent(self, event):
        self.cropSize = [self.crop.x, self.crop.y, self.crop.w, self.crop.h]

    def enterEvent(self, event):
        print('mouse')

    def leaveEvent(self, event):

        print('eft')
class Cropper(QMainWindow):
    def __init__(self, job):
        QMainWindow.__init__(self)
        self.targaLabel = 'TRUEVISION-XFILE. '
        self.readable = None
        self.job = job
        self.sl = None
        self.minWidth = None
        self.setWindowTitle("EDIT | RES: %s" % self.job.resolution)
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.setStyleSheet("background-color: rgb(50, 50, 50);")
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
            imageData = open(job.path, 'rb')
            qdata = self.loadImageFromBin(imageData)
            pixmap = QPixmap.fromImage(qdata)
            self.label.setPixmap(pixmap)
            self.minWidth = 400

        elif self.job.type == 'Sequence':
            imageData = open(os.path.join(self.job.path, self.job.content[0]), 'rb')
            qdata = self.loadImageFromBin(imageData)
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
            self.minWidth = 680

        self.vertSpacer = QSpacerItem(20, 0)
        font = QtGui.QFont('SansSerif', 12)
        self.layBottom.addItem(self.vertSpacer)

        self.tcLabel = QLabel()
        self.tcLabel.setText('00:00:00.01')
        self.tcLabel.setStyleSheet("color: white")
        self.tcLabel.setFont(font)
        self.layBottom.addWidget(self.tcLabel)

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
        [x.editingFinished.connect(self.setCoords) for x in self.coordinateEntry]
        [x.setStyleSheet("color: 'grey'; background-color: rgb(60, 63, 65)") for x in self.coordinateEntry]

        self.resetBtn = QPushButton('RESET', self)
        self.resetBtn.setStyleSheet("background-color: rgb(50, 50, 50); color: grey;")
        self.resetBtn.setMinimumWidth(32)
        self.resetBtn.clicked.connect(self.resetCropArea)

        self.layBottom.addWidget(self.resetBtn)

        if self.label.sizeHint().width() >= 1902:
            self.scrollArea.setFixedWidth(1902)
            self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            self.layTop.activate()
            self.setFixedWidth(self.lay.sizeHint().width())
        else:
            self.scrollArea.setFixedWidth(self.label.sizeHint().width())
            if self.label.sizeHint().width() <= self.minWidth - 18:
                self.setFixedWidth(self.minWidth)
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

        self.show()

        self.xwValidator = QIntValidator(0, self.label.geometry().width())
        self.yhValidator = QIntValidator(0, self.label.geometry().height())
        self.coordinateEntry[0].setValidator(self.xwValidator)
        self.coordinateEntry[1].setValidator(self.yhValidator)
        self.coordinateEntry[2].setValidator(self.xwValidator)
        self.coordinateEntry[3].setValidator(self.yhValidator)

        self.label.coordSignal.connect(self.updateCoords)
        #print('mainlayout', self.lay.sizeHint())
        #print('toplayout', self.layTop.sizeHint())
        #print('bottomlayout', self.layBottom.sizeHint())
        #print('scrollbox', self.scrollArea.frameGeometry())
        #print('image', pixmap.width(), pixmap.height())
        #print('label', self.label.sizeHint())
        #print('window', self.geometry())

    def updateCoords(self, x, y, w, h):
        self.coordinateEntry[0].setText(str(x))
        self.coordinateEntry[1].setText(str(y))
        self.coordinateEntry[2].setText(str(w))
        self.coordinateEntry[3].setText(str(h))
        self.job.crop = [x, y, w, h]

    def mouseMoveEvent(self, event):
        print('Mouse coords: ( %d : %d )' % (event.x(), event.y()))

    def loadImageFromBin(self, imageData):
        barray = QtCore.QByteArray()
        barray.append(imageData.read())
        if self.job.isTGA:
            if self.readable == None:
                if barray[-len(self.targaLabel):] == b'TRUEVISION-XFILE.\x00':
                    self.readable = True
                else:
                    self.readable = False
            for i in self.targaLabel:
                barray.append(i)
            qdata = QImage.fromData(barray, 'tga')
        else:
            qdata = QImage.fromData(barray)
            self.readable = True
        return qdata

    def resetCropArea(self):
        self.job.crop = []
        self.label.crop.setGeometry(0, 0, 0, 0)
        self.label.crop.hide()
        [x.setText('0') for x in self.coordinateEntry]

    def setCoords(self):
        coords = [x.text() for x in self.coordinateEntry]
        if not '' in coords:
            if int(coords[0]) + int(coords[2]) > self.label.geometry().width():
               self.coordinateEntry[2].setText(str(self.label.geometry().width() - int(coords[0])))
            if int(coords[1]) + int(coords[3]) > self.label.geometry().height():
               self.coordinateEntry[3].setText(str(self.label.geometry().height() - int(coords[1])))
            self.label.crop.show()
            self.label.crop.setGeometry(int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3]))
            self.job.crop = [int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])]

    def updateTC(self, frames):
        print(frames)
        hh = int(frames / 60 / 60 / self.job.fps)
        mm = int(frames / 60 / self.job.fps) - (hh * 60)
        ss = int(frames / self.job.fps) - (mm * 60) - (hh * 60 * 60)
        ff = int(frames) - (ss * self.job.fps) - (mm * 60 * self.job.fps) - (hh * 60 * 60 * self.job.fps)
        string = '%02d:%02d:%02d.%02d' % (hh, mm, ss, ff)
        self.tcLabel.setText(str(string))

    def valuechange(self):
        position = self.sl.value()
        self.updateTC(position + 1)
        try:
            if not self.readable:
                imageData = open(os.path.join(self.job.path, self.job.content[position]), 'rb')
                qdata = self.loadImageFromBin(imageData)
                pixmap = QPixmap.fromImage(qdata)
            else:
                pixmap = QPixmap(os.path.join(self.job.path, self.job.content[position]))
            self.label.setPixmap(pixmap)

        except Exception:
            print('something went wrong')

