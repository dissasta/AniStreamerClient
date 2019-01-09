import re, os, subprocess
from jobhandler import *

class Encoder(object):
    def __init__(self, job):
        self.job = job
        print(self.job)

