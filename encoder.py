import re, os, subprocess, time
from jobhandler import *
from PyQt5 import QtCore

class Encoder(QtCore.QThread):
    def __init__(self, job):
        QtCore.QThread.__init__(self)
        self.jobs = []
        self.jobs.append(job)

    def run(self):
        while self.jobs:
            time.sleep(1)
            job = self.jobs.pop(0)
            job.runJob.setStyleSheet("background-color: rgb(50, 50, 50);color: green;")

        print('encoder done')
