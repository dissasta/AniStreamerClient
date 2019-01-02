import random, re, zipfile, subprocess, os, time, lzma
from main import *
from config import *
from string import ascii_uppercase, digits
from PyQt5 import QtCore
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QApplication, QWidget
import threading

sequenceAssetTypes = ['.tga', '.png']
videoAssetTypes = ['.ani', '.mov', '.mpeg', '.mpg', '.mkv', '.avi', '.mp4', '.wmv', '.m2v', '.mxf']
archiveAssetTypes = ['.zip', '.rar', '.7z']
alphaTags = ['rgba', 'brga', 'bgra']

class Asset(object):
    def __init__(self, path):
        self.path = path
        self.status = None
        self.basename = os.path.basename(path)
        self.type = ''
        self.alpha = False
        self.resolution = None
        self.ingest = False
        if os.path.isfile(path):
            self.ext = os.path.basename(path).split('.')[-1]
        self.valid = False

    def btnstate(self, checkbox):
        print(checkbox, checkbox.isChecked())

    def genOutFilename(self):
        if self.type == 'Sequence':
            parentFolder = self.basename
            filename = self.matrix
            outputFile = filename.split('.')[0][:filename.index('%')].rstrip('_')
        else:
            parentFolder = os.path.dirname(self.path).split('\\')[-1].lower()
            filename = self.basename
            outputFile = filename.split('.')[0]
        string = 'x'

        if parentFolder == 'in' and ('_in' not in filename and ' in' not in filename):
            outputFile = outputFile + '_in'

        elif parentFolder == 'in' and ('_in' in filename or ' in' in filename):
            outputFile = outputFile

        elif parentFolder == 'out' and ('_out' not in filename and ' out' not in filename):
            outputFile = outputFile + '_out'

        elif parentFolder == 'out' and ('_out' in filename or ' out' in filename):
            outputFile = outputFile + aniExt

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

        return outputFile

class Video(Asset):
    def __init__(self, path):
        Asset.__init__(self, path)
        self.type = 'Video'
        self.toMov = False
        self.uncompress = False
        self.ffmpegTags = ['matroska', 'webm', 'qtrle', 'prores']
        self.outFilename = self.genOutFilename()

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
        self.toMov = False
        self.validFormat = False
        self.gaps = gaps
        if 'tga' in matrix.lower():
            self.ffmpegName = 'targa'
        elif 'png' in matrix.lower():
            self.ffmpegName = 'png'
        self.outFilename = self.genOutFilename()

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
        self.outFilename = self.genOutFilename()

class Archive(Asset):
    def __init__(self, path):
        Asset.__init__(self, path)
        self.tempFolderName = self.generateTempArchiveFolder()
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
        if self.ext.lower() == 'zip':
            try:
                with zipfile.ZipFile(self.path, 'r') as zip:
                    self.fileCount = len(zip.infolist())
                    for file in zip.namelist():
                        if not "_MACOSX" in file:
                            zip.extract(file, tempFolder)
                            self.counter += 1
                            self.unzipCounterUpdate(signal)
                    self.unpacked = True
                    self.status = "Unpacking successful"
                    signal.emit(self, 7, 'UNZIPPED')

            except Exception:
                print('Bad Zip File')
                self.status = "Unpacking failed"
                os.remove(tempFolder)

class JobScanner(QtCore.QThread):
    new_signal = QtCore.pyqtSignal(object)
    new_signal2 = QtCore.pyqtSignal(object, int, str)
    def __init__(self, assets):
        QtCore.QThread.__init__(self)
        self.assets = assets
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

    def run(self):
        self.createTempFolder()
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
            #self.createJobs()
            break

    def createTempFolder(self):
        if not os.path.exists(Config.tempDir):
            os.mkdir(Config.tempDir)

    def scanStructure(self, asset):
        #scan individual folders internal structure and extract separate folder paths
        if os.path.isdir(asset):
            walked = [[root, files] for root, folder, files in os.walk(asset)]
            for entry in walked:
                entry[0] = entry[0].replace('/', '\\')
                self.newFolders.append(Folder(entry[0]))
                # scan again for rogue video and archive files
                for file in entry[1]:
                    if any(file.lower().endswith(x) for x in archiveAssetTypes):
                        self.newArchives.append(Archive(os.path.join(entry[0], file)))
                    #if any(file.lower().endswith(x) for x in videoAssetTypes):
                    #    self.newVideos.append(Video(os.path.join(entry[0], file)))

        #scan individual files for import
        elif os.path.isfile(asset):
            asset = asset.replace('/', '\\')
            if any(asset.lower().endswith(x) for x in videoAssetTypes):
                self.newVideos.append(Video(asset))
            elif any(asset.lower().endswith(x) for x in sequenceAssetTypes):
                self.newStills.append(Still(asset))
            elif any(asset.lower().endswith(x) for x in archiveAssetTypes):
                self.newArchives.append(Archive(asset))

        #self.tempArchiveFolders = []
        #self.handleArchives()

    def handleArchives(self):
        #extract archives to TEMP folder
        while self.newArchives:
            archive = self.newArchives.pop(0)
            tempFolder = os.path.join(Config.tempDir, archive.tempFolderName)
            os.mkdir(tempFolder)
            self.new_signal.emit(archive)
            archive.unpack(tempFolder, self.new_signal2)

        #move each archive object from newArchives into allArchives
            self.allArchives.append(archive)

        #add new temporary folders to a list for further scanning
            self.assets.append(tempFolder)

        #scan the structure again of any of the newly created temporary archive folders
        '''if self.tempArchiveFolders:
            self.scanStructure(self.tempArchiveFolders)'''

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
            hh = int(frames/60/60/25)
            mm = int(frames/60/25) - (hh*60)
            ss = int(frames/25) - (mm*60) - (hh*60* 60)
            ff = int(frames) - (ss*25) - (mm*60*25) - (hh*60*60*25)
            string = '%02d:%02d:%02d.%02d' % (hh, mm, ss, ff)
            return(str(string))

    def scanAssets(self, items):
        #print("scanning")
        for job in items:
            self.new_signal2.emit(job, 10, job.outFilename)
            if job.type == 'Sequence':
                if job.gaps:
                    self.new_signal2.emit(job, 4, 'YES')
                else:
                    self.new_signal2.emit(job, 4, 'NO')

                self.new_signal2.emit(job, 6, self.getDuration(job))

                counter = 0
                for i in job.content:
                    file = os.path.join(job.path, i)
                    metadata = subprocess.Popen('ffmpeg -i "%s" -hide_banner' %(file), shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                    out, err = metadata.communicate()
                    err = err.decode('utf-8')

                    if not job.resolution:
                        job.resolution = re.findall('\d+x\d+', err)[0]
                        self.new_signal2.emit(job, 5, job.resolution)

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
                metadata = subprocess.Popen('ffmpeg -i "%s" -hide_banner' % (file), shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = metadata.communicate()
                err = err.decode('utf-8')
                print(err)
                if not 'decoding for stream 0 failed' in err:
                    alpha = any(x in err for x in alphaTags)
                    job.resolution = re.findall('\d+x\d+', err)[0]
                    self.new_signal2.emit(job, 5, job.resolution)

                    if not alpha:
                        job.alpha = False
                    else:
                        job.alpha = True

                    correctFormat = ("Video: %s" % job.ffmpegName) in err
                    if not correctFormat:
                        job.validFormat = False
                    else:
                        job.validFormat = True

                    self.new_signal2.emit(job, 4, '-')
                    self.new_signal2.emit(job, 6, '-')

                    if job.alpha:
                        self.new_signal2.emit(job, 7, 'DONE')
                        self.new_signal2.emit(job, 3, 'PRESENT')
                        if job.validFormat:
                            self.new_signal2.emit(job, 7, 'VALID')
                            job.valid = True
                        else:
                            self.new_signal2.emit(job, 7, 'INVALID FILE FORMAT')
                    else:
                        self.new_signal2.emit(job, 3, 'MISSING')
                        self.new_signal2.emit(job, 7, 'NO ALPHA')
                else:
                    self.new_signal2.emit(job, 7, 'BAD INPUT')

            elif job.type == 'Video':
                file = job.path
                metadata = subprocess.Popen('ffmpeg -i "%s" -hide_banner' % (file), shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = metadata.communicate()
                err = err.decode('utf-8')
                if re.findall('Stream #0:0\(\S+\): Video', err) or re.findall('Stream #0:0: Video', err):
                    alpha = any(x in err for x in alphaTags)

                    if not alpha:
                        job.alpha = False
                    else:
                        job.alpha = True

                    job.duration = re.findall('(\Duration: \S+),', err)[0].split(' ')[1]
                    self.new_signal2.emit(job, 6, job.duration)

                    job.resolution = re.findall(', (\d+x\d+)', err)[0]
                    self.new_signal2.emit(job, 5, job.resolution)

                    #correctFormat = ("Video: %s" % job.ffmpegName) in err.decode('utf-8')
                    #if not correctFormat:
                     #   job.validFormat = False
                     #   break
                    #else:
                    #    job.validFormat = True
                    self.new_signal2.emit(job, 4, '-')

                    if job.alpha:
                        self.new_signal2.emit(job, 7, 'VALID')
                        self.new_signal2.emit(job, 3, 'PRESENT')
                        job.valid = True
                    else:
                        self.new_signal2.emit(job, 3, 'MISSING')
                        self.new_signal2.emit(job, 7, 'LOCAL ONLY')

                else:
                    self.new_signal2.emit(job, 7, 'BAD INPUT')

            if job.valid:
                job.ingest.setEnabled(1)
                #print(job.ingest)

    def scanFolderForAssets(self, folder):
        for ext in sequenceAssetTypes:
            folder.content = [x for x in os.listdir(folder.path) if (x.lower().endswith(ext))]
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
                    folder.jobs.append(Still(os.path.join(folder.path, file)))

            prefixesFound = set(prefixesFound)

            #check each of the prefixes for sequence
            for prefix in prefixesFound:
                matrix = prefix[0][:prefix[1]]
                list = [file for file in folder.content if file.startswith(matrix)]
                newMatrix = (matrix + '%d0' + prefix[0][prefix[1]:])
                gaps = False
                if len(list) >= 2:
                    for i in range(1, len(list)):
                        if int(re.findall('(\d+)', list[i])[-1]) - int(re.findall('(\d+)', list[i-1])[-1]) != 1:
                            gaps = True
                            break
                        else:
                            continue

                    folder.jobs.append(Sequence(folder.path, list, newMatrix, gaps))

                else:
                    folder.jobs.append(Still(os.path.join(folder.path, list[0])))

        folder.videos = [x for x in os.listdir(folder.path) if any(x.lower().endswith(y) for y in videoAssetTypes)]

        for file in folder.videos:
            folder.jobs.append(Video(os.path.join(folder.path, file)))

        self.new_signal.emit(folder)

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

