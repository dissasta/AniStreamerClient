import re, os, subprocess, time, shutil
from jobhandler import *
from PyQt5 import QtCore
from main import *

si = subprocess.STARTUPINFO()
si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

class Encoder(QtCore.QThread):
    def __init__(self, job):
        QtCore.QThread.__init__(self)
        self.jobs = []
        self.jobs.append(job)

    def run(self):
        while self.jobs:
            #time.sleep(1)
            job = self.jobs.pop(0)
            job.runJob.setStyleSheet("background-color: rgb(50, 50, 50);color: orange;")
            job.runJob.setText('WORKING')
            AniNewRes = self.calcNewRes(job)
            hRes = AniNewRes.split('x')[0]
            vRes = AniNewRes.split('x')[1]
            if not job.crop:
                orgHRes = job.resolution.split('x')[0]
                orgVRes = job.resolution.split('x')[1]
                xPos = str(0)
                yPos = str(0)
                vPad = str(int(AniNewRes.split('x')[1]) - int(orgVRes))
                hPad = str(int(AniNewRes.split('x')[0]) - int(orgHRes))
            else:
                orgHRes = str(job.crop[2])
                orgVRes = str(job.crop[3])
                xPos = str(job.crop[0])
                yPos = str(job.crop[1])
                vPad = str(int(AniNewRes.split('x')[1]) - int(job.crop[3]))
                hPad = str(int(AniNewRes.split('x')[0]) - int(job.crop[2]))
            """
            print('orgHRes', orgHRes)
            print('orgVRes', orgVRes)
            print('x', xPos)
            print('y', yPos)
            print('hRes', hRes)
            print('vRes', vRes)
            print('hPad', hPad)
            print('vPad', vPad)
            """
            if job.type == 'Still':
                target = os.path.join(tempDir, job.outFilename.text())
                if job.format.currentText() == 'ANI':
                    target = target + '.ani'
                    encode = subprocess.Popen('ffmpeg -loop 1 -i ' + '"' + job.path + '"' + ' -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill];[0:0]alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob -t 4 ' + '"' + target + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)
                elif job.format.currentText() == 'MOV':
                    target = target + '.mov'
                    encode = subprocess.Popen('ffmpeg -loop 1 -i ' + '"' + job.path + '"' + ' -y -t 4 -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '" -pix_fmt argb -vcodec qtrle -an ' + '"' + target + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

                elif job.format.currentText() == 'PASS-THROUGH':
                    encode = None
                    target = target + job.ext
                    shutil.copyfile(job.path, target)

                elif job.format.currentText() == 'TGA':
                    target = target + '.tga'
                    encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '" -pix_fmt bgra -coder raw ' + '"' + target + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

                elif job.format.currentText() == 'PNG':
                    target = target + '.png'
                    encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '" -pix_fmt rgba -compression_level ' + str(pngCompressionLevel) + ' "' + target + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

                if encode:
                    out = encode.communicate()
                    if "no such file or directory" in out:
                        self.jobFailed(job)

            elif job.type == 'Sequence':
                source = os.path.join(job.path, job.matrix)
                target = os.path.join(tempDir, job.outFilename.text())
                if job.format.currentText() == 'ANI':
                    if extendAni:
                        self.extendSequence(job)
                    target = target + '.ani'
                    encode = subprocess.Popen('ffmpeg -start_number ' + job.firstFrame + ' -i ' + '"' + source + '"' + ' -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill];[0:0]alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob ' + '"' + target + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

                elif job.format.currentText() == 'MOV':
                    target = target + '.mov'
                    encode = subprocess.Popen('ffmpeg -start_number ' + job.firstFrame + ' -i ' + '"' + source + '"' + ' -y -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '" -pix_fmt argb -vcodec qtrle -an ' + '"' + target + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

                elif job.format.currentText() == "PNG SEQUENCE 2xFPS":
                    target = os.path.join(tempDir, job.outFilename.text())
                    if not os.path.exists(target):
                        os.mkdir(target)
                    output = os.path.join(target, job.outFilename.text() + '_%05d.png')
                    encode = subprocess.Popen('ffmpeg -start_number ' + job.firstFrame + ' -i ' + '"' + source + '"' + ' -y -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ', setpts=2.0*PTS" -pix_fmt rgba -compression_level ' + str(pngCompressionLevel) + ' "' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

                out = encode.communicate()

            elif job.type == 'Video':
                target = os.path.join(tempDir, job.outFilename.text())
                if job.format.currentText() == 'ANI':
                    target = target + '.ani'
                    encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:0]pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill];[0:0]alphaextract,pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob ' + '"' + target + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

                elif job.format.currentText() == 'MOV':
                    target = target + '.mov'
                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -i ' + '"' + job.path + '"' + ' -y -filter_complex [0:0][1:1]alphamerge -pix_fmt argb -vcodec qtrle -hide_banner ' + '"' + target + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)
                    else:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -pix_fmt argb -vcodec qtrle -an ' + '"' + target + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

                elif job.format.currentText() == 'CH5-MXF':
                    target = target + '.mxf'
                    encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -pix_fmt yuv422p -vcodec mpeg2video -non_linear_quant 1 -flags +ildct+ilme -intra_vlc 1 -qmax 3 -lmin "1*QP2LAMBDA" -rc_max_vbv_use 1 -rc_min_vbv_use 1 -g 1 -b:v 50000k -minrate 50000k -maxrate 50000k -bufsize 8000k -an ' + '"' + target + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

                elif job.format.currentText() == 'PNG SEQUENCE':
                    target = os.path.join(tempDir, job.outFilename.text())
                    if not os.path.exists(target):
                        os.mkdir(target)
                    output = os.path.join(target, job.outFilename.text() + '_%05d.png')
                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -i ' + '"' + job.path + '"' + ' -y -filter_complex [0:0][1:1]alphamerge -pix_fmt rgba -compression_level ' + str(pngCompressionLevel) + ' "' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)
                    else:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -pix_fmt rgba -compression_level ' + str(pngCompressionLevel) + ' "' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

                elif job.format.currentText() == 'TGA SEQUENCE':
                    target = os.path.join(tempDir, job.outFilename.text())
                    if not os.path.exists(target):
                        os.mkdir(target)
                    output = os.path.join(target, job.outFilename.text() + '_%05d.tga')
                    if job.alpha:
                        pix_fmt = 'bgra'
                    else:
                        pix_fmt = 'rgb24'
                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -i ' + '"' + job.path + '"' + ' -y -filter_complex [0:0][1:1]alphamerge -pix_fmt ' + pix_fmt + ' -coder raw ' + '"' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)
                    else:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -pix_fmt ' + pix_fmt + ' -coder raw ' + '"' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

                elif job.format.currentText() == 'PNG SEQUENCE 2xFPS':
                    target = os.path.join(tempDir, job.outFilename.text())
                    if not os.path.exists(target):
                        os.mkdir(target)
                    output = os.path.join(target, job.outFilename.text() + '_%05d.png')
                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -i ' + '"' + job.path + '"' + ' -y -filter_complex [0:0][1:1]alphamerge,setpts=2.0*PTS -pix_fmt rgba -compression_level ' + str(pngCompressionLevel) + ' "' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)
                    else:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -pix_fmt rgba -filter:v setpts=2.0*PTS -compression_level ' + str(pngCompressionLevel) + ' "' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

                elif job.format.currentText() == 'PASS-THROUGH':
                    encode = None
                    target = os.path.join(tempDir, job.outFilename.text()) + job.ext
                    shutil.copyfile(job.path, target)

                if encode:
                    out = encode.communicate()
                    if "no such file or directory" in out:
                        self.jobFailed(job)

            if not job.failed:
                try:
                    if job.ingest.isChecked():
                        shutil.move(target, os.path.join(outputDir, os.path.basename(target)))
                        self.jobDone(job)
                    else:
                        dest = os.path.join(outputDir, os.path.basename(target))
                        if os.path.exists(dest):
                            if os.path.isdir(dest):
                                shutil.rmtree(dest)
                            elif os.path.isfile(dest):
                                os.remove(dest)
                        shutil.move(target, dest)
                        self.jobDone(job)
                except Exception:
                    pass
                    #print('couldn\'t move files')

            #time.sleep(1)
        #print('encoder done')

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
        job.runJob.update()

    def jobFailed(self, job):
        job.failed = True
        JobScanner.new_signal2(job, 7, 'INPUT ERROR')
        job.runJob.setStyleSheet("background-color: rgb(50, 50, 50);color: red;")
        job.runJob.setText('FAILED')
        job.runJob.update()

    def calcNewRes(self, job):
        try:
            if not job.crop:
                width = int(job.resolution.split('x')[0])
                height = int(job.resolution.split('x')[1])
                while width % 16 != 0:
                    width += 1
                while height % 16 != 0:
                    height += 1
            else:
                width = int(job.crop[2])
                height = int(job.crop[3])
                while width % 16 != 0:
                    width += 1
                while height % 16 != 0:
                    height += 1
            return str(width) + 'x' + str(height)
        except Exception:
            #print('failed to re-calculate resolution')
            return None