from jobhandler import *
import time
from PyQt5 import QtCore
from main import *

class Receiver(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        while True:
            print('elo')
        # print(Client.socket)
        #Client.socket.recv(1024)


class Sender(QtCore.QThread):
    def __init__(self, clientSocket):
        QtCore.QThread.__init__(self)
        self.socket = clientSocket

    def run(self):
        while True:
            time.sleep(1)
            if Job.jobs:
                myJob = Job.jobs.pop(0)
                self.socket.send((str(myJob.size) + '|' + myJob.fileName).encode('utf-8'))
                time.sleep(2)
                sentData = 0
                with open(myJob.path, 'rb') as file:
                    data = file.read(buffSize)
                    while data:
                        self.socket.send(data)
                        sentData += len(data)
                        print(str(int(100/(int(myJob.size)/sentData))) + '%')
                        data = file.read(buffSize)
                    print('done sending')
