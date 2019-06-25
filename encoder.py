import re, os, subprocess, time, shutil
from jobhandler import *
from PyQt5 import QtCore
from main import *

si = subprocess.STARTUPINFO()
si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

class Encoder(QtCore.QThread):
    progressBarPass = QtCore.pyqtSignal(int, int, bool)
    def __init__(self, job):
        QtCore.QThread.__init__(self)
        self.jobs = []
        self.jobs.append(job)

    def run(self):
        while self.jobs:
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
                temp = os.path.join(tempDir, job.outFilename.text())
                if job.format.currentText() == 'ANI':
                    temp = temp + '.ani'
                    encode = subprocess.Popen('ffmpeg -loop 1 -i ' + '"' + job.path + '"' + ' -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill];[0:0]alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob -t 2 ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                elif job.format.currentText() == 'MOV':
                    temp = temp + '.mov'
                    encode = subprocess.Popen('ffmpeg -loop 1 -i ' + '"' + job.path + '"' + ' -y -t 2 -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '" -pix_fmt argb -vcodec qtrle -an ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'PASS-THROUGH':
                    encode = None
                    temp = temp + job.ext
                    shutil.copyfile(job.path, temp)

                elif job.format.currentText() == 'TGA':
                    temp = temp + '.tga'
                    encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '" -pix_fmt bgra -coder raw ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'PNG':
                    temp = temp + '.png'
                    encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '" -pix_fmt rgba -compression_level ' + str(pngCompressionLevel) + ' "' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                if encode:
                    out = ''
                    for line in encode.stderr:
                        out += line
                        frames = re.findall('frame= +\d+', line)
                        if frames:
                            self.progressBarPass.emit(50, int(re.findall('\d+', frames[0])[0]), True)
                    if "no such file or directory" in out:
                        self.jobFailed(job)

            elif job.type == 'Sequence':
                source = os.path.join(job.path, job.matrix)
                for i in range(len(job.segments)):
                    job.segments[i][0] += job.ffmpegFrameOffset
                    job.segments[i][1] += job.ffmpegFrameOffset
                    if len(job.segments) > 1:
                        temp = os.path.join(tempDir, job.outFilename.text() + '_seg' + str(i + 1))
                    else:
                        temp = os.path.join(tempDir, job.outFilename.text())

                    if job.format.currentText() == 'ANI':
                        temp += '.ani'
                        job.segments[i].append(temp)
                        if job.segments[i][2]:
                            encode = subprocess.Popen('ffmpeg -f lavfi -i color=c=black:s=' + hRes + 'x' + vRes + ':r=25:d=0.08 -f lavfi -i color=c=black:s=' + hRes + 'x' + vRes + ':r=25:d=0.08 -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -filter_complex "[2:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black,concat=n=2[fill];[2:0]alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black,concat=n=2[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -f vob -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                        else:
                            encode = subprocess.Popen('ffmpeg -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -start_number ' + str(job.segments[i][1]) + ' -t 0.04'+ ' -i ' + '"' + source + '"' + ' -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill1];[0:0]alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[key1];[1:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill2];[1:0]alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[key2];[fill1][fill2]concat[fill],[key1][key2]concat[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                    if job.format.currentText() == 'WEBM-VP9':
                        temp += '.webm'
                        job.segments[i].append(temp)
                        if job.segments[i][2]:
                            orgHRes = self.makeResEven(int(orgHRes), 2)
                            orgVRes = self.makeResEven(int(orgVRes), 2)
                            encode = subprocess.Popen('ffmpeg -f lavfi -i color=c=black:s=' + orgHRes + 'x' + orgVRes + ':r=25:d=0.04 -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -filter_complex "[1:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '[one];[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos +',colorkey=black[two];[one][two]concat[out]" -y -pix_fmt yuva420p -vcodec libvpx-vp9 -hide_banner -q:v ' + str(aniQFactor) + ' -b:v 5000k -map [out] ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                        else:
                            encode = subprocess.Popen('ffmpeg -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -y -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '" -pix_fmt yuva420p -vcodec libvpx-vp9 -hide_banner -q:v ' + str(aniQFactor) + ' -b:v 5000k ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                    elif job.format.currentText() == 'ANI-MATTE':
                        temp += '.ani'
                        job.segments[i].append(temp)
                        if job.segments[i][2]:
                            encode = subprocess.Popen('ffmpeg -f lavfi -i color=c=black:s=' + hRes + 'x' + vRes + ':r=25:d=0.08 -f lavfi -i color=c=black:s=' + hRes + 'x' + vRes + ':r=25:d=0.08 -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -f lavfi -i color=c=white:s=' + hRes + 'x' + vRes + ':r=25:d=' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -filter_complex "[2:0]alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill1];[3:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[key1];[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill2];[1:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[key2];[fill1][fill2]concat[fill],[key1][key2]concat[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -f vob -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                        else:
                            encode = subprocess.Popen('ffmpeg -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -start_number ' + str(job.segments[i][1]) + ' -t 0.04'+ ' -i ' + '"' + source + '"' + ' -f lavfi -i color=c=white:s=' + hRes + 'x' + vRes + ':r=25:d=' + str(float(job.segments[i][1] - job.segments[i][0] + 2) / 25) + ' -filter_complex "[0:0]alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill1];[1:0]alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[fill2];[2:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[key];[fill1][fill2]concat[fill]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                    elif job.format.currentText() == 'ANI-INV-MATTE':
                        temp += '.ani'
                        job.segments[i].append(temp)
                        if job.segments[i][2]:
                            encode = subprocess.Popen('ffmpeg -f lavfi -i color=c=black:s=' + hRes + 'x' + vRes + ':r=25:d=0.08 -f lavfi -i color=c=black:s=' + hRes + 'x' + vRes + ':r=25:d=0.08 -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -f lavfi -i color=c=white:s=' + hRes + 'x' + vRes + ':r=25:d=' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -filter_complex "[2:0]alphaextract,negate,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill1];[3:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[key1];[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill2];[1:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[key2];[fill1][fill2]concat[fill],[key1][key2]concat[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -f vob -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                        else:
                            encode = subprocess.Popen('ffmpeg -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -start_number ' + str(job.segments[i][1]) + ' -t 0.04'+ ' -i ' + '"' + source + '"' + ' -f lavfi -i color=c=white:s=' + hRes + 'x' + vRes + ':r=25:d=' + str(float(job.segments[i][1] - job.segments[i][0] + 2) / 25) + ' -filter_complex "[0:0]alphaextract,negate,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill1];[1:0]alphaextract,negate,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad + ':y=' + vPad + ':color=black[fill2];[2:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[key];[fill1][fill2]concat[fill]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                    elif job.format.currentText() == 'MOV':
                        temp += '.mov'
                        orgHRes = self.makeResEven(int(orgHRes), 4)
                        job.segments[i].append(temp)
                        if job.segments[i][2]:
                            encode = subprocess.Popen('ffmpeg -f lavfi -i color=c=black:s=' + hRes + 'x' + vRes + ':r=25:d=0.04 -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -y -filter_complex "[1:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '[fill1];[0:0]colorkey=black,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '[fill2];[fill1][fill2]concat[out]' + '" -pix_fmt argb -vcodec qtrle -an -map "[out]" ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                        else:
                            encode = subprocess.Popen('ffmpeg -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -y -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '" -pix_fmt argb -vcodec qtrle -an ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                    elif job.format.currentText() == 'MOV-MATTE':
                        temp += '.mov'
                        orgHRes = self.makeResEven(int(orgHRes), 4)
                        job.segments[i].append(temp)
                        if job.segments[i][2]:
                            encode = subprocess.Popen('ffmpeg -f lavfi -i color=c=black:s=' + hRes + 'x' + vRes + ':r=25:d=0.04 -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -y -filter_complex "[1:0]alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '[fill1];[0:0]colorkey=black,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '[fill2];[fill1][fill2]concat[out]' + '" -pix_fmt gray -vcodec qtrle -an -map "[out]" ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                        else:
                            encode = subprocess.Popen('ffmpeg -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -y -filter_complex "[0:0]alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '" -pix_fmt gray -vcodec qtrle -an ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                    elif job.format.currentText() == 'MOV-INV-MATTE':
                        temp += '.mov'
                        orgHRes = self.makeResEven(int(orgHRes), 4)
                        job.segments[i].append(temp)
                        if job.segments[i][2]:
                            encode = subprocess.Popen('ffmpeg -f lavfi -i color=c=black:s=' + hRes + 'x' + vRes + ':r=25:d=0.04 -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -y -filter_complex "[1:0]alphaextract,negate,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '[fill1];[0:0]colorkey=black,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '[fill2];[fill1][fill2]concat[out]' + '" -pix_fmt gray -vcodec qtrle -an -map "[out]" ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                        else:
                            encode = subprocess.Popen('ffmpeg -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -y -filter_complex "[0:0]alphaextract,negate,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '" -pix_fmt gray -vcodec qtrle -an ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                    elif job.format.currentText() == "PNG SEQUENCE 2xFPS":
                        if len(job.segments) == 1:
                            temp = os.path.join(tempDir, job.outFilename.text())
                        else:
                            temp = os.path.join(tempDir, job.outFilename.text() + '_seg' + str(i + 1))
                        job.segments[i].append(temp)

                        if not os.path.exists(temp):
                            os.mkdir(temp)
                        output = os.path.join(temp, job.outFilename.text() + '_%05d.png')
                        encode = subprocess.Popen('ffmpeg -start_number ' + str(job.segments[i][0]) + ' -t ' + str(float(job.segments[i][1] - job.segments[i][0] + 1) / 25) + ' -i ' + '"' + source + '"' + ' -y -filter_complex "[0:0]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ', setpts=2.0*PTS" -pix_fmt rgba -compression_level ' + str(pngCompressionLevel) + ' "' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                    #out = encode.communicate()
                    if encode:
                        out = ''
                        for line in encode.stderr:
                            out += line
                            frames = re.findall('frame= +\d+', line)
                            if frames:
                                if job.format.currentText() == "PNG SEQUENCE 2xFPS":
                                    self.progressBarPass.emit(((job.segments[i][1] - job.segments[i][0] + 1) * 2) - 1, int(re.findall('\d+', frames[0])[0]), True)
                                else:
                                    self.progressBarPass.emit(job.segments[i][1] - job.segments[i][0] + 1, int(re.findall('\d+', frames[0])[0]), True)
                        if "no such file or directory" in out:
                            self.jobFailed(job)

            elif job.type == 'Video':
                temp = os.path.join(tempDir, job.outFilename.text())
                if job.format.currentText() == 'ANI':
                    temp += '.ani'
                    encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:' + job.streamID + ']crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill];[0:' + job.streamID + ']alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'ANI-MATTE':
                    temp += '.ani'
                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:1]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill];[0:1]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                    else:
                        encode = subprocess.Popen('ffmpeg ' + job.ffmpegDecoderString + '-i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:' + job.streamID + ']alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[fill];[0:' + job.streamID + ']alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'ANI-INV-MATTE':
                    temp += '.ani'
                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:1]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black,negate[fill];[0:1]crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black,negate[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                    else:
                        encode = subprocess.Popen('ffmpeg ' + job.ffmpegDecoderString + '-i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:' + job.streamID + ']alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black,negate[fill];[0:' + job.streamID + ']alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',pad=width=' + hRes + ':height=' + vRes + ':x=' + hPad +':y=' + vPad + ':color=black,negate[key]" -y -vcodec mpeg2video -pix_fmt yuv422p -hide_banner -map "[fill]" -map "[key]" -q:v ' + str(aniQFactor) + ' -b:v 5000k -f vob ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'WEBM-VP9':
                    temp += '.webm'
                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -i ' + '"' + job.path + '"' + ' -y -filter_complex [0:0][1:1]alphamerge,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ' -pix_fmt yuva420p -vcodec libvpx-vp9 -hide_banner -q:v ' + str(aniQFactor) + ' -b:v 5000k ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                    else:
                        encode = subprocess.Popen('ffmpeg ' + job.ffmpegDecoderString + '-i ' + '"' + job.path + '"' + ' -y -filter_complex [0:' + job.streamID + ']crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ' -pix_fmt yuva420p -vcodec libvpx-vp9 -hide_banner -q:v ' + str(aniQFactor) + ' -b:v 5000k ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'MOV':
                    temp += '.mov'
                    orgHRes = self.makeResEven(int(orgHRes), 4)
                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -i ' + '"' + job.path + '"' + ' -y -filter_complex [0:0][1:1]alphamerge,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ' -pix_fmt argb -vcodec qtrle -hide_banner ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                    else:
                        encode = subprocess.Popen('ffmpeg ' + job.ffmpegDecoderString + '-i ' + '"' + job.path + '"' + ' -y -filter_complex [0:' + job.streamID + ']crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ' -pix_fmt argb -vcodec qtrle -an ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'MOV-MATTE':
                    temp += '.mov'
                    orgHRes = self.makeResEven(int(orgHRes), 4)
                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -filter_complex crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ' -map 0:1 -pix_fmt gray -vcodec qtrle -an -hide_banner ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                    else:
                        encode = subprocess.Popen('ffmpeg ' + job.ffmpegDecoderString + '-i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:' + job.streamID + ']alphaextract,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '[key]" -pix_fmt gray -vcodec qtrle -map [key]-an -hide_banner ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'MOV-INV-MATTE':
                    temp += '.mov'
                    orgHRes = self.makeResEven(int(orgHRes), 4)
                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:1]negate,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '[key]" -pix_fmt gray -vcodec qtrle -map [key]-an -hide_banner ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                    else:
                        encode = subprocess.Popen('ffmpeg ' + job.ffmpegDecoderString + '-i ' + '"' + job.path + '"' + ' -y -filter_complex "[0:' + job.streamID + ']alphaextract,negate,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + '[key]" -pix_fmt gray -vcodec qtrle -map [key]-an -hide_banner ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'CH5-MXF':
                    temp += '.mxf'
                    encode = subprocess.Popen('ffmpeg ' + job.ffmpegDecoderString + '-i ' + '"' + job.path + '"' + ' -y -filter_complex [0:' + job.streamID + ']crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ' -pix_fmt yuv422p -vcodec mpeg2video -non_linear_quant 1 -flags +ildct+ilme -intra_vlc 1 -qmax 3 -lmin "1*QP2LAMBDA" -rc_max_vbv_use 1 -rc_min_vbv_use 1 -g 1 -q:v 1 -b:v 50000k -minrate 50000k -maxrate 50000k -bufsize 8000k -an ' + '"' + temp + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'PNG SEQUENCE':
                    temp = os.path.join(tempDir, job.outFilename.text())
                    if not os.path.exists(temp):
                        os.mkdir(temp)
                    output = os.path.join(temp, job.outFilename.text() + '_%05d.png')

                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -i ' + '"' + job.path + '"' + ' -y -filter_complex [0:0][1:1]alphamerge,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ' -pix_fmt rgba -compression_level ' + str(pngCompressionLevel) + ' "' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                    else:
                        encode = subprocess.Popen('ffmpeg ' + job.ffmpegDecoderString + '-i ' + '"' + job.path + '"' + ' -y -filter_complex [0:' + job.streamID + ']crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ' -pix_fmt rgba -compression_level ' + str(pngCompressionLevel) + ' "' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'TGA SEQUENCE':
                    temp = os.path.join(tempDir, job.outFilename.text())
                    if not os.path.exists(temp):
                        os.mkdir(temp)
                    output = os.path.join(temp, job.outFilename.text() + '_%05d.tga')
                    if job.alpha:
                        pix_fmt = 'bgra'
                    else:
                        pix_fmt = 'rgb24'
                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -i ' + '"' + job.path + '"' + ' -y -filter_complex [0:0][1:1]alphamerge,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ' -pix_fmt ' + pix_fmt + ' -coder raw ' + '"' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                    else:
                        encode = subprocess.Popen('ffmpeg ' + job.ffmpegDecoderString + '-i ' + '"' + job.path + '"' + ' -y -filter_complex [0:' + job.streamID + ']crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ' -pix_fmt ' + pix_fmt + ' -coder raw ' + '"' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'PNG SEQUENCE 2xFPS':
                    temp = os.path.join(tempDir, job.outFilename.text())
                    if not os.path.exists(temp):
                        os.mkdir(temp)
                    output = os.path.join(temp, job.outFilename.text() + '_%05d.png')
                    if job.isANI:
                        encode = subprocess.Popen('ffmpeg -i ' + '"' + job.path + '"' + ' -i ' + '"' + job.path + '"' + ' -y -filter_complex [0:0][1:1]alphamerge,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ',setpts=2.0*PTS -pix_fmt rgba -compression_level ' + str(pngCompressionLevel) + ' "' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)
                    else:
                        encode = subprocess.Popen('ffmpeg ' + job.ffmpegDecoderString + '-i ' + '"' + job.path + '"' + ' -y -filter_complex [0:' + job.streamID + ']setpts=2.0*PTS,crop=' + orgHRes + ':' + orgVRes + ':' + xPos + ':' + yPos + ' -pix_fmt rgba -compression_level ' + str(pngCompressionLevel) + ' "' + output + '"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si, universal_newlines=True)

                elif job.format.currentText() == 'PASS-THROUGH':
                    encode = None
                    temp = os.path.join(tempDir, job.outFilename.text()) + job.ext
                    shutil.copyfile(job.path, temp)

                if encode:
                    out = ''
                    for line in encode.stderr:
                        out += line
                        frames = re.findall('frame= +\d+', line)
                        if frames:
                            if job.format.currentText() == 'PNG SEQUENCE 2xFPS':
                                self.progressBarPass.emit((int(job.frameCount) * 2) - 1, int(re.findall('\d+', frames[0])[0]), True)
                            else:
                                self.progressBarPass.emit(int(job.frameCount), int(re.findall('\d+', frames[0])[0]), True)
                    if "no such file or directory" in out:
                        self.jobFailed(job)

            if not job.failed:
                self.jobDone(job)
                try:
                    if job.type == 'Sequence':
                        temp = [x[3] for x in job.segments]
                    else:
                        temp = [temp]

                    for t in temp:
                        dest = os.path.join(outputDir, os.path.basename(t))
                        if os.path.exists(dest):
                            if os.path.isdir(dest):
                                shutil.rmtree(dest)
                            elif os.path.isfile(dest):
                                os.remove(dest)
                        shutil.move(t, dest)
                except Exception:
                    pass
                    #print('couldn\'t move files')


        self.progressBarPass.emit(100, 100, False)

    def extendSequence(self, job):
        lastFrame = sorted(job.content)[-1]
        found = re.findall('(\d+)\.', lastFrame)[-1]
        newFrame = lastFrame.replace(found, str(int(found) + 1).zfill(len(found)))
        shutil.copy(os.path.join(job.path, lastFrame), os.path.join(job.path, newFrame))
        if os.path.isfile(os.path.join(job.path, newFrame)):
            job.content.append(newFrame)
        job.extended = True

    def removeLastFrame(self, job):
        lastFrame = sorted(job.content)[-1]
        if os.path.isfile(os.path.join(job.path, lastFrame)):
            os.remove(os.path.join(job.path, lastFrame))

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

    def makeResEven(self, val, div):
        while val % div != 0:
            if val < div:
                val = div
            else:
                val -= 1

        return str(val)