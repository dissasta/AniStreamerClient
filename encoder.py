import re, os, subprocess, time, shutil
from jobhandler import *
from PyQt5 import QtCore
from main import *

class Encoder(QtCore.QThread):
    def __init__(self, job):
        QtCore.QThread.__init__(self)
        self.jobs = []
        self.jobs.append(job)

    def run(self):
        while self.jobs:
            #time.sleep(1)
            job = self.jobs.pop(0)
            print(job, job.outFilename.text())
            job.runJob.setStyleSheet("background-color: rgb(50, 50, 50);color: orange;")
            job.runJob.setText('WORKING')
            AniNewRes = self.calcNewRes(job)

            if AniNewRes:
                hRes = AniNewRes.split('x')[0]
                vRes = AniNewRes.split('x')[1]
                vPad = str(int(AniNewRes.split('x')[1]) - int(job.resolution.split('x')[1]))
                hPad = str(int(AniNewRes.split('x')[0]) - int(job.resolution.split('x')[0]))
            else:
                hRes = job.resolution.split('x')[0]
                vRes = job.resolution.split('x')[1]
                vPad = str(0)
                hPad = str(0)

            if job.type == 'Still':
                destFile = os.path.join(tempDir, job.outFilename.text())
                if job.format.currentText() == 'ANI':
                    destFile = destFile + '.ani'
                    encode = subprocess.Popen('ffmpeg -loop 1 -i ' + '"' + job.path + '"' + ' -filter_complex "[0:0]pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill];[0:0]alphaextract,pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob -t 4 ' + '"' + destFile + '"', shell=True, stderr=subprocess.PIPE)
                elif job.format.currentText() == 'MOV':
                    destFile = destFile + '.mov'
                    encode = subprocess.Popen('ffmpeg -loop 1 -i ' + '"' + job.path + '"' + ' -y -t 4 -pix_fmt argb -vcodec qtrle -an ' + '"' + destFile + '"', shell=True, stderr=subprocess.PIPE)
                elif job.format.currentText() == 'PASS-THROUGH':
                    encode = None
                    destFile = destFile + job.ext
                    shutil.copyfile(job.path, destFile)
                elif job.format.currentText() == 'TGA':
                    destFile = destFile + '.tga'
                    encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -pix_fmt bgra -coder raw ' + '"' + destFile + '"', shell=True, stderr=subprocess.PIPE)
                elif job.format.currentText() == 'PNG':
                    destFile = destFile + '.png'
                    encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -pix_fmt rgba -compression_level ' + str(pngCompressionLevel) + ' "' + destFile + '"', shell=True, stderr=subprocess.PIPE)

                if encode:
                    out = encode.communicate()
                    if "no such file or directory" in out:
                        self.jobFailed(job)

            elif job.type == 'Sequence':
                source = os.path.join(job.path, job.matrix)
                destFile = os.path.join(tempDir, job.outFilename.text())
                if job.format.currentText() == 'ANI':
                    if extendAni:
                        self.extendSequence(job)
                    destFile = destFile + '.ani'
                    encode = subprocess.Popen('ffmpeg -i ' + '"' + source + '"' + ' -filter_complex "[0:0]pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill];[0:0]alphaextract,pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob ' + '"' + destFile + '"', shell=True, stderr=subprocess.PIPE)
                elif job.format.currentText() == 'MOV':
                    destFile = destFile + '.mov'
                    encode = subprocess.Popen('ffmpeg -i ' + '"' + source + '"' + ' -y -pix_fmt argb -vcodec qtrle -an ' + '"' + destFile + '"', shell=True, stderr=subprocess.PIPE)
                elif job.format.currentText() == "PNG 2xFPS":
                    destFile = destFile + '%05d.png'
                    encode = subprocess.Popen('ffmpeg -i ' + '"' + source + '"' + ' -y -pix_fmt rgba -filter:v setpts=2.0*PTS ' + '"' + destFile + '"', shell=True, stderr=subprocess.PIPE)
                out = encode.communicate()

            elif job.type == 'Video':
                pass

            if not job.failed:
                if job.ingest.isChecked():
                    shutil.move(destFile, os.path.join(outputDir, os.path.basename(destFile)))
                    self.jobDone(job)
                else:
                    shutil.move(destFile, os.path.join(outputDir, os.path.basename(destFile)))
                    self.jobDone(job)

            #time.sleep(1)
        print('encoder done')

    def extendSequence(self, job):
        lastFrame = sorted(job.content)[-1]
        found = re.findall('(\d+)\.', lastFrame)[-1]
        newFrame = lastFrame.replace(found, str(int(found) + 1).zfill(len(found)))
        shutil.copy(os.path.join(job.path, lastFrame), os.path.join(job.path, newFrame))
        if os.path.isfile(os.path.join(job.path, newFrame)):
            job.content.append(newFrame)

    def jobDone(self, job):
        #JobScanner.new_signal2(job, 7, 'COMPLETE')
        job.runJob.setStyleSheet("background-color: rgb(50, 50, 50);color: green;")
        job.runJob.setText('DONE')

    def jobFailed(self, job):
        job.failed = True
        JobScanner.new_signal2(job, 7, 'INPUT ERROR')
        job.runJob.setStyleSheet("background-color: rgb(50, 50, 50);color: red;")
        job.runJob.setText('FAILED')

    def calcNewRes(self, job):
        try:
            width = int(job.resolution.split('x')[0])
            height = int(job.resolution.split('x')[1])
            while width % 16 != 0:
                width += 1
            while height % 16 != 0:
                height += 1
            return str(width) + 'x' + str(height)
        except Exception:
            print('failed to re-calculate resolution')
            return None