from main import *
from jobhandler import *
from PyQt5.QtWidgets import QLabel, QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QSlider, QSpacerItem, QLineEdit, QPushButton, QToolTip
from PyQt5.QtGui import QPixmap, QMouseEvent, QImage, QIntValidator
import os, time, binascii, cv2
from PyQt5 import QtCore

class MyLabel(QLabel):
    coordSignal = QtCore.pyqtSignal(int, int, int, int)
    def __init__(self):
        QLabel.__init__(self)
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.crop = QLabel(self)
        self.crop.setGeometry(0,0,0,0)
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
        self.coordSignal.emit(0,0,0,0)
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
        pass

    def leaveEvent(self, event):
        pass

class Cropper(QMainWindow):
    def __init__(self, parent, job):
        QMainWindow.__init__(self, parent)
        self.TGAfooter = b'\x00\x00\x00\x00\x00\x00\x00\x00TRUEVISION-XFILE.\x00'
        self.TGAcolourMap = {9: b'\x01', 10: b'\x02', 11: b'\x03'}
        self.parent = parent
        self.readable = False
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
        self.iconBase64 = b"AAABAAEAQEAAAAEAIAAoQgAAFgAAACgAAABAAAAAgAAAAAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJycndCcnJ9InJydQJycnAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACsrK2grKyv/KSkp/ycnJ8gnJydGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAsLCxKLCws/ywsLP8rKyv/KSkp/ycnJ8AnJyc8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsLCwsLP8sLCz/LCws/ywsLP8rKyv/KCgo/ycnJ7QnJycyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwsLA4sLCz/LCws/ywsLP8sLCz/LCws/ywsLP8rKyv/KCgo/CcnJ6onJycqAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCws7iwsLP8sLCz/LCws/ywsLP8sLCz/LCws/ywsLP8rKyv/enp6/M3NzaDNzc0iAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwsLNAsLCz/LCws/ywsLP8sLCz/LCws/ywsLP8sLCz/cnJy//X19f/t7e3/19fX+M3NzZbMzMwaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA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AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASUnmTEpK585KSuj8S0vo5kxM6XhMTOoEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/3//////////H/////////8H/////////wH/////////AH////////8AH////////wAH////////AAH///////8AAH///////4AAP///////gAAP//////+AAAP//////4AAA///////gAAB//////+AAAD//////4AAAH//////gAAAf/////+AAAA//////8AAAB//////wAAAH//////AAAAP/////8AAAAf/////wAAAB//////AAAAD/////8AAAAH/////4AAAAP/////wAAAA//////AAAAB/////+AAAAD/////8AAAAP/////wAAAAf/////gAAAA//////AAAAD/////+AAAAH/////4AAAAP/////wAAAA//////gAAAB/////+AAAAD/////8AAAAH/////4AAAAf/////gAAAA//////AAAAB/////+AAAAD/////4AAAAP/////wAAAAf/////gAAAB//////AAAAD/////8AAAAH/////4AAAAP/////wAAAA//////AAAAD/////+AAAAP/////8AAAA//////wAAAD//////gAAA//////+AAAH//////8AAA///////4AAP///////wAB////////gAf///////+AD////////8A/////////4H/////////x///8="
        self.setWindowIcon(iconFromBase64(self.iconBase64))
        self.font = QtGui.QFont('SansSerif', 11)

        if self.job.type == 'Video':
            self.minWidth = 400
            self.vc = cv2.VideoCapture(self.job.path)

            if self.vc.isOpened():
                pixmap = self.getVideoFrameData(0)
                self.label.setPixmap(pixmap)
            else:
                rval = False
                cv2.waitKey(1)
            #vc.release()

            self.sl = QSlider(Qt.Horizontal)
            self.sl.setMaximum(200)
            self.sl.setValue(0)
            self.sl.setTickPosition(QSlider.TicksBelow)

            if self.job.fps:
                self.sl.setTickInterval(job.fps)
            else:
                self.sl.setTickInterval(25)

            self.layBottom.addWidget(self.sl)
            self.sl.valueChanged.connect(self.valuechange)
            self.sl.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
            self.minWidth = 770

            self.vertSpacer = QSpacerItem(20, 0)
            self.layBottom.addItem(self.vertSpacer)

            self.tcLabel = QLabel()
            self.tcLabel.setText('00:00:00.01')
            self.tcLabel.setStyleSheet("color: grey")
            self.tcLabel.setFont(self.font)
            self.layBottom.addWidget(self.tcLabel)

            self.layBottom.addItem(self.vertSpacer)

        elif self.job.type == 'Still':
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
            self.minWidth = 770

            self.vertSpacer = QSpacerItem(20, 0)
            self.layBottom.addItem(self.vertSpacer)

            self.tcLabel = QLabel()
            self.tcLabel.setText('00:00:00.01')
            self.tcLabel.setStyleSheet("color: grey")
            self.tcLabel.setFont(self.font)
            self.layBottom.addWidget(self.tcLabel)

            self.layBottom.addItem(self.vertSpacer)

        self.coordinateLabels =  [QLabel(x) for x in ["<font color='grey'>X:</font>", "<font color='grey'>Y:</font>", "<font color='grey'>W:</font>", "<font color='grey'>H:</font>"]]
        self.coordinateEntry = [QLineEdit(x) for x in ['0', '0', '0', '0']]
        [x.setFont(self.font) for x in self.coordinateLabels]
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

        if self.job.type == 'Sequence':

            self.addBlackLabel = QPushButton('APPEND BLACK', self)
            if not self.job.appendBlack:
                self.addBlackLabel.setStyleSheet("background-color: rgb(50, 50, 50); color: grey;")
            else:
                self.addBlackLabel.setStyleSheet("background-color: rgb(50, 50, 50); color: green;")
            self.addBlackLabel.setFixedWidth(100)
            self.addBlackLabel.clicked.connect(self.appendBlack)
            self.layBottom.addWidget(self.addBlackLabel)

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
            self.sl.setFixedWidth(self.geometry().width()/4)

        self.show()

        self.xwValidator = QIntValidator(0, self.label.geometry().width())
        self.yhValidator = QIntValidator(0, self.label.geometry().height())
        self.coordinateEntry[0].setValidator(self.xwValidator)
        self.coordinateEntry[1].setValidator(self.yhValidator)
        self.coordinateEntry[2].setValidator(self.xwValidator)
        self.coordinateEntry[3].setValidator(self.yhValidator)

        self.label.coordSignal.connect(self.updateCoords)

        if self.job.crop:
            self.coordinateEntry[0].setText(str(self.job.crop[0]))
            self.coordinateEntry[1].setText(str(self.job.crop[1]))
            self.coordinateEntry[2].setText(str(self.job.crop[2]))
            self.coordinateEntry[3].setText(str(self.job.crop[3]))
            self.label.crop.setGeometry(self.job.crop[0], self.job.crop[1], self.job.crop[2], self.job.crop[3])
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

    def loadImageFromBin(self, imageData):
        header = QtCore.QByteArray()
        barray = QtCore.QByteArray()

        if self.job.isTGA:
            header.append(imageData.read(18))
            width = int(binascii.b2a_hex(header[13] + header[12]), 16)
            height = int(binascii.b2a_hex(header[15] + header[14]), 16)
            RLE = int(binascii.b2a_hex(header[2]), 16) in range(9, 12)
            alpha = int(binascii.b2a_hex(header[16]), 16) == 32

            for i in range(len(header)):
                if i == 2 and RLE:
                    barray.append(self.TGAcolourMap[int(binascii.b2a_hex(header[2]), 16)])
                else:
                    barray.append(header[i])

            if alpha:
                pixelData = 4
            else:
                pixelData = 3

            pxlCount = width * height
            pxlTotal = 0

            if not RLE:
                barray.append(imageData.read())
            else:
                while pxlTotal != pxlCount:
                    rCount = int(binascii.b2a_hex(imageData.read(1)), 16)
                    if rCount >= 128:
                        rCount = abs((rCount & 0xF0) - 128) + (rCount & 0x0F) + 1

                        pixels = imageData.read(pixelData) * rCount
                        barray.append(pixels)

                    else:
                        rCount += 1
                        for i in range(rCount):
                            pixel = imageData.read(pixelData)
                            barray.append(pixel)

                    pxlTotal += rCount

                barray.append(imageData.read())

            if not self.readable:
                if barray[-len(self.TGAfooter):] != self.TGAfooter:
                    barray.append(self.TGAfooter)
                else:
                    self.readable = True

            qdata = QImage.fromData(barray, 'tga')

        else:
            barray.append(imageData.read())
            qdata = QImage.fromData(barray)
            self.readable = True

        return qdata

    def resetCropArea(self):
        self.job.crop = []
        self.label.crop.setGeometry(0, 0, 0, 0)
        self.label.crop.hide()
        [x.setText('0') for x in self.coordinateEntry]

    def appendBlack(self):
        if self.job.appendBlack:
            self.job.appendBlack = False
            self.addBlackLabel.setStyleSheet("background-color: rgb(50, 50, 50); color: grey;")
        else:
            self.job.appendBlack = True
            self.addBlackLabel.setStyleSheet("background-color: rgb(50, 50, 50); color: green;")

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
            if self.job.type == 'Video':
                pixmap = self.getVideoFrameData(position)
            else:
                if not self.readable:
                    imageData = open(os.path.join(self.job.path, self.job.content[position]), 'rb')
                    qdata = self.loadImageFromBin(imageData)
                    pixmap = QPixmap.fromImage(qdata)
                else:
                    pixmap = QPixmap(os.path.join(self.job.path, self.job.content[position]))
            self.label.setPixmap(pixmap)

        except Exception:
            pass
            #print('something went wrong')

    def getVideoFrameData(self, frameID):
        self.vc.set(1,frameID)
        rval, frame = self.vc.read(cv2.IMREAD_UNCHANGED)
        imgData = cv2.imencode('.png', frame)[1].tostring()
        qdata = QImage.fromData(imgData)
        return QPixmap.fromImage(qdata)