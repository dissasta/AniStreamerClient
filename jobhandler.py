import random, re, zipfile, subprocess, os, time, shutil, rarfile, tarfile, binascii
from main import *
from encoder import *
from config import *
from string import ascii_uppercase, digits
from PyQt5 import QtCore
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QApplication, QWidget

sequenceAssetTypes = ['.tga', '.png']
videoAssetTypes = ['.ani', '.mov', '.mpeg', '.mpg', '.mkv', '.avi', '.mp4', '.wmv', '.m2v', '.mxf', '.webm', '.flv']
archiveAssetTypes = ['.zip', '.tar', '.rar', '.7z']
alphaTags = ['rgba', 'brga', 'bgra', 'argb', 'yuva420p', 'alpha_mode      : 1']

si = subprocess.STARTUPINFO()
si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

if not unRARPresent:
    archiveAssetTypes.remove('.rar')
if not sevenZipPresent:
    archiveAssetTypes.remove('.7z')

class Asset(object):
    def __init__(self, path):
        self.path = path
        self.status = None
        self.basename = os.path.basename(path)
        self.type = ''
        self.alpha = False
        self.resolution = None
        self.crop = []
        self.ingest = False
        if os.path.isfile(path):
            self.ext = '.' + os.path.basename(path).split('.')[-1]
        self.valid = False
        self.outFilename = None
        self.targetPath = None
        self.runJob = None
        self.failed = False
        self.fps = None
        self.frameCount = None
        self.ingestable = False
        self.extended = False
        self.segments = []
        self.ffmpegFrameOffset = 0

    def btnstate(self):
        if self.ingest:
            self.fillFormats()

    def reverifyFilename(self):
        if len(self.outFilename.text()) > 35:
            self.outFilename.setStyleSheet("color: rgb(244, 41, 65);")
        else:
            self.outFilename.setStyleSheet("color: grey;")

    def toggleRunJobButton(self):
        self.outFilename.setText(''.join(ch for ch in self.outFilename.text() if ch not in '<>:"/\|?*!,.^@$&#()=+{}[];:%s~`' %"'"))
        self.reverifyFilename()

        if self.format.currentText() and self.outFilename.text():
            self.runJob.setEnabled(1)
            self.runJob.setStyleSheet("background-color: rgb(50, 50, 50); color: gold;")
        else:
            self.runJob.setEnabled(0)
            self.runJob.setStyleSheet("background-color: rgb(50, 50, 50); color: grey;")

    def fillFormats(self):
        self.format.clear()
        self.runJob.setEnabled(0)
        self.runJob.setStyleSheet("background-color: rgb(50, 50, 50); color: grey;")
        if self.ingest.isChecked():
            for format in self.ingestFormats:
                self.format.addItem(format)
            return

        if self.alpha and self.valid:
            for format in self.localFormatsAlpha:
                self.format.addItem(format)

        else:
            if self.localFormatsNoAlpha:
                for format in self.localFormatsNoAlpha:
                    self.format.addItem(format)
            else:
                self.format.setDisabled(1)

    def genOutFilename(self):
        if self.type == 'Sequence':
            parentFolder = self.basename
            filename = self.matrix
            outputFile = filename.split('.')[0][:filename.index('%')].rstrip('_')
        else:
            parentFolder = os.path.dirname(self.path).split('\\')[-1].lower()
            filename = self.basename
            outputFile = filename.split('.')[0]

        if parentFolder == 'in' and ('_in' not in filename and ' in' not in filename):
            outputFile = outputFile + '_in'

        elif parentFolder == 'in' and ('_in' in filename or ' in' in filename):
            outputFile = outputFile

        elif parentFolder == 'out' and ('_out' not in filename and ' out' not in filename):
            outputFile = outputFile + '_out'

        elif parentFolder == 'out' and ('_out' in filename or ' out' in filename):
            outputFile = outputFile + '_out'

        else:
            if ('_in' in parentFolder or ' in' in parentFolder) and ('in' not in filename and '_in' not in filename):
                outputFile = outputFile + '_in'

            elif ('_in' in parentFolder or ' in' in parentFolder) and (' in' in filename or '_in' in filename):
                outputFile = outputFile

            elif ('_out' in parentFolder or ' out' in parentFolder) and (
                    ' out' not in filename and '_out' not in filename):
                outputFile = outputFile + '_out'

            elif ('_out' in parentFolder or ' out' in parentFolder) and (' out' in filename or '_out' in filename):
                outputFile = outputFile

        outputFile = str(outputFile.rstrip().lstrip())

        return (''.join(ch for ch in outputFile if ch not in '<>:"/\|?*!,.^@$&#()=+{}[];:%s~`' %"'"))
        #return outputFile.rstrip().lstrip()

class Video(Asset):
    def __init__(self, path):
        Asset.__init__(self, path)
        self.type = 'Video'
        self.uncompress = False
        self.fps = None
        self.ffmpegDecoderString = ''
        self.format = None
        self.isANI = False
        self.isWEBM = False
        self.isFLV = False
        self.streamID = '0'
        self.localFormatsAlpha = ['', 'ANI', 'ANI-MATTE', 'ANI-INV-MATTE', 'WEBM-VP9', 'MOV', 'MOV-MATTE', 'MOV-INV-MATTE', 'CH5-MXF', 'PNG SEQUENCE', 'TGA SEQUENCE', 'PNG SEQUENCE 2xFPS']
        self.localFormatsNoAlpha = ['', 'CH5-MXF', 'PNG SEQUENCE', 'TGA SEQUENCE', 'PNG SEQUENCE 2xFPS']
        self.ingestFormats = ['', 'ANI', 'WEBM-VP9', 'MOV']

class Folder(Asset):
    def __init__(self, path):
        Asset.__init__(self, path)
        self.ext = ''
        self.content = []
        self.videos = []
        self.prefixesFound = []
        self.jobs = []

class Sequence(Asset):
    def __init__(self, path, content, matrix, gaps):
        Asset.__init__(self, path)
        self.type = 'Sequence'
        self.content = content
        self.matrix = matrix
        self.fps = 25
        self.isTGA = False
        self.isPNG = False
        self.validFormat = False
        self.gaps = gaps
        self.appendBlack = False
        if 'tga' in matrix.lower():
            self.ffmpegName = 'targa'
        elif 'png' in matrix.lower():
            self.ffmpegName = 'png'
        self.format = None
        self.localFormatsAlpha = ['', 'ANI', 'ANI-MATTE', 'ANI-INV-MATTE', 'WEBM-VP9', 'MOV', 'MOV-MATTE', 'MOV-INV-MATTE', 'PNG SEQUENCE 2xFPS']
        self.localFormatsNoAlpha = []
        self.ingestFormats = ['', 'ANI', 'WEBM-VP9', 'MOV']

class Still(Asset):
    def __init__(self, path):
        Asset.__init__(self, path)
        self.type = 'Still'
        self.toAni = False
        self.validFormat = False
        if 'tga' in self.basename.lower():
            self.ffmpegName = 'targa'
        elif 'png' in self.basename.lower():
            self.ffmpegName = 'png'
        self.format = None
        self.isTGA = False
        self.isPNG = False
        self.localFormatsAlpha = ['', 'ANI', 'MOV', 'TGA', 'PNG', 'WEBP']
        self.localFormatsNoAlpha = []
        self.ingestFormats = ['', 'PASS-THROUGH', 'ANI', 'MOV']

class Archive(Asset):
    def __init__(self, path):
        Asset.__init__(self, path)
        self.tempFolderName = self.generateTempArchiveFolder()
        self.tempFolderPath = os.path.join(tempDir, self.tempFolderName)
        self.fileCount = 0
        self.counter = 0
        self.unpacked = False
        self.type = 'Archive'

    def generateTempArchiveFolder(self):
        return ''.join(random.choices(ascii_uppercase + digits, k=8))

    def unzipCounterUpdate(self, signal):
        percentage = int(100 / (self.fileCount / self.counter))
        signal.emit(self, 7, str(percentage) + '%')

    def unpack(self, tempFolder, signal):
        if self.ext.lower() == '.zip':
            #print('here')
            try:
                with zipfile.ZipFile(self.path, 'r') as zip:
                    self.fileCount = len(zip.infolist())
                    for file in zip.namelist():
                        if not "_MACOSX" in file:
                            zip.extract(file, tempFolder)
                            self.counter += 1
                            self.unzipCounterUpdate(signal)
                    self.unpacked = True
                    signal.emit(self, 7, 'EXTRACTED')

            except Exception:
                pass
                #print('Bad ZIP File')

        elif self.ext.lower() == '.rar':
            try:
                with rarfile.RarFile(self.path, 'r') as rar:
                    content = [name for name in rar.namelist() if not '_MACOSX' in name]
                    self.fileCount = len(content)
                    for file in content:
                        rar.extract(file, tempFolder)
                        self.counter += 1
                        self.unzipCounterUpdate(signal)
                    self.unpacked = True
                    signal.emit(self, 7, 'EXTRACTED')

            except Exception:
                pass
                #print('Bad RAR File')

        elif self.ext.lower() == '.tar':
            try:
                with tarfile.TarFile(self.path, 'r') as tar:
                    content = [name for name in tar.getnames() if not '_MACOSX' in name]
                    self.fileCount = len(content)
                    for file in content:
                        tar.extract(file, tempFolder)
                        self.counter += 1
                        self.unzipCounterUpdate(signal)
                    self.unpacked = True
                    signal.emit(self, 7, 'EXTRACTED')

            except Exception:
                pass
                #print('Bad TAR File')

        elif self.ext.lower() == '.7z':
            try:
                with lzma.open(self.path, 'r') as szip:
                    content = [name for name in szip.getnames() if not '_MACOSX' in name]
                    self.fileCount = len(content)
                    for file in content:
                        tar.extract(file, tempFolder)
                        self.counter += 1
                        self.unzipCounterUpdate(signal)
                    self.unpacked = True
                    signal.emit(self, 7, 'EXTRACTED')

            except Exception:
                pass
                #print('Bad TAR File')

class JobScanner(QtCore.QThread):
    new_signal = QtCore.pyqtSignal(object)
    new_signal2 = QtCore.pyqtSignal(object, int, str)
    #jobsReadySignal = QtCore.pyqtSignal(int)
    progressBar = QtCore.pyqtSignal(int, int, bool)
    def __init__(self, parent, assets):
        QtCore.QThread.__init__(self)
        self.assets = assets
        self.parent = parent
        self.sequences = []
        self.newArchives = []
        self.newStills = []
        self.newVideos = []
        self.newFolders = []
        self.allArchives = []
        self.allVideos = []
        self.allStills = []
        self.allFolders = []
        self.tempArchiveFolders = []
        self.completeJobs = []
        self.ready = False
        self.encoder = None

    def run(self):
        self.createFolders()
        while True:
            while self.assets:
                for i in range(len(self.assets)):
                    asset = self.assets.pop()
                    self.scanStructure(asset)
                while self.newFolders:
                    folder = self.newFolders.pop(0)
                    self.scanFolderForAssets(folder)
                    self.allFolders.append(folder)
                self.handleStills()
                self.handleVideos()
                self.handleArchives()

            for folder in self.allFolders:
                  self.scanAssets(folder.jobs)
            self.scanAssets(self.allStills)
            self.scanAssets(self.allVideos)
            self.ready = True
            #self.jobsReadySignal.emit(1)
            break
            #time.sleep(5)
            #for i in self.allFolders:
            #    for job in i.jobs:
            #        print(job.outFilename.text())

    def createFolders(self):
        if not os.path.exists(tempDir):
            os.mkdir(tempDir)
        if not os.path.exists(outputDir):
            os.mkdir(outputDir)

    def scanStructure(self, asset):
        #scan individual folders internal structure and extract separate folder paths
        if os.path.isdir(asset):
            walked = [[root, files] for root, folder, files in os.walk(asset)]
            for entry in sorted(walked, reverse = True):
                if not '_MACOSX' in entry[0]:
                    entry[0] = entry[0].replace('/', '\\')
                    self.newFolders.insert(0, Folder(entry[0]))
                    # scan again for rogue video and archive files
                    for file in entry[1]:
                        if any(file.lower().endswith(x) for x in archiveAssetTypes):
                            self.newArchives.insert(0, Archive(os.path.join(entry[0], file)))
                        #if any(file.lower().endswith(x) for x in videoAssetTypes):
                        #    self.newVideos.append(Video(os.path.join(entry[0], file)))
        #scan individual files for import
        elif os.path.isfile(asset):
            asset = asset.replace('/', '\\')
            if any(asset.lower().endswith(x) for x in videoAssetTypes):
                self.newVideos.insert(0, Video(asset))
            elif any(asset.lower().endswith(x) for x in sequenceAssetTypes):
                self.newStills.insert(0, Still(asset))
            elif any(asset.lower().endswith(x) for x in archiveAssetTypes):
                self.newArchives.insert(0, Archive(asset))

    def handleArchives(self):
        #extract archives to TEMP folder
        for archive in self.newArchives:
            if not os.path.exists(archive.tempFolderPath):
                os.mkdir(archive.tempFolderPath)
            self.tempArchiveFolders.append(archive.tempFolderPath)
            self.new_signal.emit(archive)

        while self.newArchives:
            archive = self.newArchives.pop(0)
            archive.unpack(archive.tempFolderPath, self.new_signal2)

            # move each archive object from newArchives into allArchives|might not be needed
            self.allArchives.append(archive)

            # add new temporary folders to a list for further scanning
            if archive.unpacked:
                self.assets.append(archive.tempFolderPath)
            else:
                self.new_signal2.emit(archive, 7, 'CORRUPTED?')
                shutil.rmtree(archive.tempFolderPath, ignore_errors=True)

    def handleStills(self):
        while self.newStills:
            still = self.newStills.pop(0)
            self.new_signal.emit(still)
            self.allStills.append(still)

    def handleVideos(self):
        while self.newVideos:
            video = self.newVideos.pop(0)
            self.new_signal.emit(video)
            self.allVideos.append(video)

    def getDuration(self, job):
        if job.type == 'Sequence':
            frames = len(job.content)
            job.frameCount = frames
            job.segments.append([1, frames, 0])
            hh = int(frames/60/60/25)
            mm = int(frames/60/25) - (hh*60)
            ss = int(frames/25) - (mm*60) - (hh*60* 60)
            ff = int(frames) - (ss*25) - (mm*60*25) - (hh*60*60*25)
            string = '%02d:%02d:%02d.%02d' % (hh, mm, ss, ff)
            return(str(string))

        #might need to look into ffmpeg announced durations as they seem off sometimes
        if job.type == 'Video' and job.frameCount:
            frames = job.frameCount
            job.segments.append([1, frames, 0])
            hh = int(frames/60/60/job.fps)
            mm = int(frames/60/job.fps) - (hh*60)
            ss = int(frames/job.fps) - (mm*60) - (hh*60* 60)
            ff = round(float(frames - (ss*job.fps) - (mm*60*job.fps) - (hh*60*60*job.fps)))
            string = '%02d:%02d:%02d.%02d' % (hh, mm, ss, ff)
            return(str(string))

    def getFrameCount(self, job):
        try:
            hh, mm, ss, ms = re.findall('\d+', job.duration)
            job.frameCount = round(float(((int(hh) * 60 * 60) + (int(mm) * 60) + int(ss)) * job.fps + (int(ms) * 10 / (1000/job.fps))))
        except Exception:
            pass
            #print('not a proper duration')

    def scanAssets(self, items):
        #print("scanning")
        for job in items:
            #self.new_signal2.emit(job, 10, job.outFilename)
            if job.type == 'Sequence':
                if job.gaps:
                    self.new_signal2.emit(job, 4, 'YES')
                else:
                    self.new_signal2.emit(job, 4, 'NO')

                self.new_signal2.emit(job, 6, self.getDuration(job))
                job.firstFrame = re.findall('(\d+)\.', job.content[0])[-1]
                job.ffmpegFrameOffset = int(job.firstFrame) - 1

                counter = 0
                for i in job.content:
                    if counter == 0:

                        file = os.path.join(job.path, i)
                        metadata = subprocess.Popen(['ffmpeg', '-i', file, '-hide_banner'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)
                        out, err = metadata.communicate()
                        err = err.decode('utf-8')

                        if not job.resolution:
                            job.resolution = re.findall('\d+x\d+', err)[-1]
                            self.new_signal2.emit(job, 5, job.resolution)

                        if job.content[0].split('.')[-1].lower() == 'tga' and "Video: targa" in err:
                            job.isTGA = True
                        elif job.content[0].split('.')[-1].lower() == 'png' and "Video: png" in err:
                            job.isPNG = True

                        alpha = any(x in err for x in alphaTags)
                        if not alpha:
                            job.alpha = False
                            break
                        else:
                            job.alpha = True

                        correctFormat = (("Video: %s" % job.ffmpegName) in err)
                        if not correctFormat:
                            job.validFormat = False
                            break
                        else:
                            job.validFormat = True
                            if job.isTGA:
                                with open(file, 'rb') as input:
                                    testHeader = binascii.hexlify(input.read(18))
                            elif job.isPNG:
                                with open(file, 'rb') as input:
                                    testHeader = binascii.hexlify(input.read(29))
                    else:
                        if job.isTGA:
                            file = os.path.join(job.path, i)
                            with open(file, 'rb') as input:
                                header = binascii.hexlify(input.read(18))

                            if header != testHeader:
                                job.alpha = False
                                job.valid = False
                                break

                        elif job.isPNG:
                            file = os.path.join(job.path, i)
                            with open(file, 'rb') as input:
                                header = binascii.hexlify(input.read(29))

                            if header != testHeader:
                                job.alpha = False
                                job.valid = False
                                break

                    counter += 1
                    percentage = int(100/(len(job.content)/counter))
                    self.new_signal2.emit(job, 3, str(percentage) + '%')
                    self.new_signal2.emit(job, 7, 'SCANNING')

                if job.alpha:
                    self.new_signal2.emit(job, 7, 'DONE')
                    self.new_signal2.emit(job, 3, 'PRESENT')
                    if job.validFormat:
                        self.new_signal2.emit(job, 7, 'VALID')
                        job.valid = True
                        job.ingestable = True
                        if job.gaps:
                            job.valid = False
                            self.new_signal2.emit(job, 7, 'INVALID')
                    else:
                        self.new_signal2.emit(job, 7, 'INVALID FILE FORMAT')

                else:
                    self.new_signal2.emit(job, 3, 'MISSING')
                    self.new_signal2.emit(job, 7, 'INVALID')

            elif job.type == 'Still':
                file = job.path
                metadata = subprocess.Popen(['ffmpeg', '-i', file, '-hide_banner'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)
                out, err = metadata.communicate()
                err = err.decode('utf-8')
                if not 'decoding for stream 0 failed' in err:
                    alpha = any(x in err for x in alphaTags)
                    job.resolution = re.findall('\d+x\d+', err)[-1]
                    self.new_signal2.emit(job, 5, job.resolution)

                    if not alpha:
                        job.alpha = False
                    else:
                        job.alpha = True

                    if job.basename.split('.')[-1].lower() == 'tga' and "Video: targa" in err:
                        job.validFormat = True
                        job.isTGA = True
                        job.ingestFormats.insert(2, 'PNG')

                    elif job.basename.split('.')[-1].lower() == 'png' and "Video: png" in err:
                        job.validFormat = True
                        job.isPNG = True
                        job.ingestFormats.insert(2, 'TGA')

                    self.new_signal2.emit(job, 4, '-')
                    self.new_signal2.emit(job, 6, '-')

                    if job.alpha:
                        self.new_signal2.emit(job, 7, 'DONE')
                        self.new_signal2.emit(job, 3, 'PRESENT')
                        if job.validFormat:
                            self.new_signal2.emit(job, 7, 'VALID')
                            job.valid = True
                            job.ingestable = True
                        else:
                            self.new_signal2.emit(job, 7, 'INVALID FILE FORMAT')
                    else:
                        self.new_signal2.emit(job, 3, 'MISSING')
                        self.new_signal2.emit(job, 7, 'INVALID')
                else:
                    self.new_signal2.emit(job, 7, 'BAD INPUT')

            elif job.type == 'Video':
                file = job.path
                metadata = subprocess.Popen(['ffmpeg', '-i', file, '-hide_banner'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)
                out, err = metadata.communicate()
                err = err.decode('utf-8')
                aniCondition = re.findall('Stream #0:0\[\S+\]: Video', err) and re.findall('Stream #0:1\[\S+\]: Video', err)
                webmCondition = re.findall('Stream #0:0: Video: vp8', err) or re.findall('Stream #0:0: Video: vp9', err) or re.findall('Stream #0:0\(\S+\): Video: vp9', err) or re.findall('Stream #0:0\(\S+\): Video: vp8', err)
                FLVCondition = re.findall('Stream #0:1: Video: vp6a', err) or re.findall('Stream #0:1: Video: vp6f', err)

                if re.findall('Stream #0:0\(\S+\): Video|Stream #0:0: Video|Stream #0:1\(\S+\): Video', err) or aniCondition or FLVCondition:
                    job.valid = True
                    alpha = any(x in err for x in alphaTags)

                    if not alpha and not aniCondition:
                        job.alpha = False
                    else:
                        job.alpha = True

                    fps = re.findall('(\d+.\d+ fps)|(\d+ fps)', err)
                    if fps:
                        for entry in fps[0]:
                            if entry:
                                try:
                                    job.fps = float(entry.split(' ')[0])
                                    break
                                except Exception:
                                    pass
                                    #print('FPS count not a float')

                    job.duration = re.findall('(\Duration: \S+),', err)[0].split(' ')[1]

                    if job.fps and job.duration != 'NA':
                        self.getFrameCount(job)

                    if job.frameCount:
                        job.duration = self.getDuration(job)

                    if job.ext == '.ani' and aniCondition:
                        job.isANI = True
                        job.ingestFormats[1] = 'PASS-THROUGH'
                        job.localFormatsAlpha.remove('ANI')

                    if job.ext == '.webm' and webmCondition:
                        job.isWEBM = True
                        if 'vp9' in webmCondition[0]:
                            job.ffmpegDecoderString = '-vcodec libvpx-vp9 '
                        else:
                            job.ffmpegDecoderString = '-vcodec libvpx '
                        job.ingestFormats[1] = 'PASS-THROUGH'
                        job.localFormatsAlpha.remove('WEBM-VP9')

                    if job.ext == '.flv' and FLVCondition:
                        job.isFLV = True
                        job.streamID = '1'
                        if 'vp6a' in FLVCondition[0]:
                            job.ffmpegDecoderString = '-vcodec vp6a '
                        else:
                            job.ffmpegDecoderString = '-vcodec vp6f '
                        job.ingestFormats[1] = 'PASS-THROUGH'

                    self.new_signal2.emit(job, 6, job.duration)

                    job.resolution = re.findall(', (\d+x\d+)', err)[0]
                    self.new_signal2.emit(job, 5, job.resolution)
                    self.new_signal2.emit(job, 4, '-')

                    if job.alpha:
                        self.new_signal2.emit(job, 7, 'VALID')
                        self.new_signal2.emit(job, 3, 'PRESENT')
                        job.ingestable = True
                    else:
                        self.new_signal2.emit(job, 3, 'MISSING')
                        self.new_signal2.emit(job, 7, 'LOCAL ONLY')

                else:
                    self.new_signal2.emit(job, 7, 'BAD INPUT')

            if job.valid:
                job.edit.setEnabled(1)
                job.edit.setStyleSheet("background-color: rgb(50, 50, 50); color: gold;")
                job.fillFormats()
                filename = job.genOutFilename()
                if len(filename) > 40:
                    job.outFilename.setStyleSheet("color: rgb(244, 41, 65);")
                job.outFilename.setText(filename)
                job.outFilename.setCursorPosition(0)
                job.outFilename.setEnabled(1)

            if job.ingestable:
                job.ingest.setEnabled(1)
                #print(job.path)

    def scanFolderForAssets(self, folder):
        for ext in sequenceAssetTypes:
            folder.content = sorted([x for x in os.listdir(folder.path) if (x.lower().endswith(ext))])
            prefixesFound = []
            #check folder's internal structure for individual image prefixes
            for file in folder.content:
                numbers = re.findall('(\d+)\.', file)
                if numbers:
                    numSuffix = numbers[-1]
                    numSuffixIdx = file.rfind(numSuffix)
                    file = file[:numSuffixIdx] + str(len(numSuffix)) + file[numSuffixIdx + len(numSuffix):]
                    prefixesFound.append((file, numSuffixIdx))
                else:
                    folder.jobs.insert(0, Still(os.path.join(folder.path, file)))

            prefixesFound = set(prefixesFound)

            #check each of the prefixes for sequence
            for prefix in prefixesFound:
                matrix = prefix[0][:prefix[1]]
                list = [file for file in folder.content if file.startswith(matrix)]
                number = re.findall('(\d+)', prefix[0])[-1]
                newMatrix = (matrix + '%' + str(number).zfill(2) + 'd' + prefix[0][prefix[1] + len(number):])
                gaps = False
                if len(list) >= 2:
                    for i in range(1, len(list)):
                        if int(re.findall('(\d+)', list[i])[-1]) - int(re.findall('(\d+)', list[i-1])[-1]) != 1:
                            gaps = True
                            break
                        else:
                            continue

                    folder.jobs.insert(0, Sequence(folder.path, list, newMatrix, gaps))

                else:
                    folder.jobs.insert(0, Still(os.path.join(folder.path, list[0])))

        folder.videos = [x for x in os.listdir(folder.path) if any(x.lower().endswith(y) for y in videoAssetTypes)]

        for file in folder.videos:
            folder.jobs.append(Video(os.path.join(folder.path, file)))

        self.new_signal.emit(folder)

    def removeJobFromList(self, job):
        if job in self.allStills:
            self.allStills.remove(job)
        elif job in self.allVideos:
            self.allVideos.remove(job)
        else:
            for folder in self.allFolders:
                if job in folder.jobs:
                    folder.jobs.remove(job)
                    break

    def processJob(self, job):
        workedOn = False
        if self.encoder:
            if job.runJob.isEnabled():
                self.encoder.jobs.append(job)
                workedOn = True
                if self.encoder.isFinished():
                    self.encoder.start()
        else:
            if job.runJob.isEnabled():
                self.encoder = Encoder(job)
                self.encoder.start()
                self.encoder.progressBarPass.connect(self.progressBarPass)
                workedOn = True

        if workedOn:
            job.ingest.setEnabled(0)
            job.edit.setEnabled(0)
            job.format.setEnabled(0)
            job.outFilename.setEnabled(0)
            job.runJob.setEnabled(0)
            job.runJob.setStyleSheet("background-color: rgb(50, 50, 50);color: orange;")
            job.runJob.setText('QUEUED')
            return True

    def processAll(self):
        toRemove = []
        for job in self.allStills + self.allVideos:
            removable = self.processJob(job)
            if removable:
                toRemove.append(job)

        for folder in self.allFolders:
            for job in folder.jobs:
                removable = self.processJob(job)
                if removable:
                    toRemove.append(job)

        for job in toRemove:
            self.removeJobFromList(job)

    def progressBarPass(self, max, current, visible):
        self.progressBar.emit(max, current, visible)

class Job(object):
    jobs = []
    def __init__(self, type, path, ext):
        self.type = type
        self.path = path
        self.fileName = None
        self.ext = ext
        self.size = None
        self.target = None
        #Job.jobs.append(self)

