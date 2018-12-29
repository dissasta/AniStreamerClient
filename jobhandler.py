import random, re, zipfile, subprocess, os, time, lzma
from config import *
from string import ascii_uppercase, digits
from PyQt5 import QtCore
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QApplication, QWidget

encodeAssetTypes = ['.mov', '.tga', '.png']
videoAssetTypes = ['.ani', '.mov', '.mpeg', '.mpg', '.mkv', '.avi']
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
        if os.path.isfile(path):
            self.ext = os.path.basename(path).split('.')[-1]
        self.valid = False

class Video(Asset):
    def __init__(self, path):
        Asset.__init__(self, path)
        self.type = 'Video'
        self.toMov = False
        self.ingest = False
        self.uncompress = False

class Folder(Asset):
    def __init__(self, path):
        Asset.__init__(self, path)
        self.ext = ''
        self.content = []
        self.prefixesFound = []
        self.jobs = []

class Sequence(Asset):
    def __init__(self, path, content, matrix, gaps):
        Asset.__init__(self, path)
        self.type = 'Sequence'
        self.content = content
        self.matrix = matrix
        self.toMov = False
        self.ingest = False
        self.validFormat = False
        self.gaps = gaps
        if 'tga' in matrix.lower():
            self.ffmpegName = 'targa'
        elif 'png' in matrix.lower():
            self.ffmpegName = 'png'

class Still(Asset):
    def __init__(self, path):
        Asset.__init__(self, path)
        self.type = 'Still'
        self.toAni = False
        self.ingest = False
        self.validFormat = False
        if 'tga' in self.basename.lower():
            self.ffmpegName = 'targa'
        elif 'png' in self.basename.lower():
            self.ffmpegName = 'png'

class Archive(Asset):
    def __init__(self, path):
        Asset.__init__(self, path)
        self.tempFolderName = self.generateTempArchiveFolder()
        self.unpacked = False
        self.type = 'Archive'

    def generateTempArchiveFolder(self):
        return ''.join(random.choices(ascii_uppercase + digits, k=8))

    def unpack(self, tempFolder):
        if self.ext.lower() == 'zip':
            try:
                with zipfile.ZipFile(self.path, 'r') as zip:
                    for file in zip.namelist():
                        zip.extract(file, tempFolder)
                        self.unpacked = True
                        self.status = "Unpacking successful"
                # with zip.open('eggs.txt') as myfile:
                #   print(myfile.read())
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
        self.stills = []
        self.sequences = []
        self.newArchives = []
        self.allArchives = []
        self.videos = []
        self.folders = []
        self.tempArchiveFolders = []

    def run(self):
        self.createTempFolder()
        self.scanStructure(self.assets)
        self.scanFolderForSequences()
        self.handleStills()
        self.handleVideos()
        self.scanAssets()
        #self.createJobs()

    def createTempFolder(self):
        if not os.path.exists(Config.tempDir):
            os.mkdir(Config.tempDir)

    def scanStructure(self, assets):
        #scan individual folders internal structure and extract separate folder paths
        for asset in assets:
            if os.path.isdir(asset):
                 walked = [[root, files] for root, folder, files in os.walk(asset)]
                 for entry in walked:
                     entry[0] = entry[0].replace('/', '\\')
                     self.folders.append(Folder(entry[0]))
                     # scan again for rogue video and archive files
                     for file in entry[1]:
                        if any(x in file.lower() for x in archiveAssetTypes):
                            self.newArchives.append(Archive(os.path.join(entry[0], file)))
                        if any(x in file.lower() for x in videoAssetTypes):
                            self.videos.append(Video(os.path.join(entry[0], file)))

            #scan individual files for import
            elif os.path.isfile(asset):
                asset = asset.replace('/', '\\')
                if any(x in asset.lower() for x in videoAssetTypes):
                    self.videos.append(Video(asset))
                elif any(x in asset.lower() for x in encodeAssetTypes[1:]):
                    self.stills.append(Still(asset))
                elif any(x in asset.lower() for x in archiveAssetTypes):
                    self.newArchives.append(Archive(asset))

        self.tempArchiveFolders = []
        self.handleArchives()

    def handleArchives(self):
        #extract archives to TEMP folder
        while self.newArchives:
            archive = self.newArchives.pop(0)
            tempFolder = os.path.join(Config.tempDir, archive.tempFolderName)
            os.mkdir(tempFolder)
            archive.unpack(tempFolder)

        #move each archive object from newArchives into allArchives
            self.allArchives.append(archive)

        #add new temporary folders to a list for further scanning
            self.tempArchiveFolders.append(tempFolder)

        #scan the structure again of any of the newly created temporary archive folders
        if self.tempArchiveFolders:
            self.scanStructure(self.tempArchiveFolders)

    def handleStills(self):
        for still in self.stills:
            self.new_signal.emit(still)

    def handleVideos(self):
        for video in self.videos:
            self.new_signal.emit(video)

    def getDuration(self, job):
        if job.type == 'Sequence':
            frames = len(job.content)
            hh = int(frames/60/60/25)
            mm = int(frames/60/25) - (hh*60)
            ss = int(frames/25) - (mm*60) - (hh*60* 60)
            ff = int(frames) - (ss*25) - (mm*60*25) - (hh*60*60*25)
            string = '%02d:%02d:%02d.%02d' % (hh, mm, ss, ff)
            return(str(string))

    def scanAssets(self):
        for folder in self.folders:
            for job in folder.jobs:
                if job.type == 'Sequence':
                    if job.gaps:
                        self.new_signal2.emit(job, 4, 'YES')
                    else:
                        self.new_signal2.emit(job, 4, 'NO')

                    self.new_signal2.emit(job, 6, self.getDuration(job))

                    counter = 0
                    for i in job.content:
                        file = os.path.join(job.path, i)
                        metadata = subprocess.Popen('ffmpeg -i %s -hide_banner' %(file), shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                        out, err = metadata.communicate()

                        if not job.resolution:
                            job.resolution = re.findall('\d+x\d+', err.decode('ascii'))[0]
                            self.new_signal2.emit(job, 5, job.resolution)

                        alpha = any(x in err.decode('ascii') for x in alphaTags)
                        if not alpha:
                            job.alpha = False
                            break
                        else:
                            job.alpha = True

                        correctFormat = ("Video: %s" % job.ffmpegName) in err.decode('ascii')
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
                    metadata = subprocess.Popen('ffmpeg -i %s -hide_banner' % (file), shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                    out, err = metadata.communicate()
                    alpha = any(x in err.decode('ascii') for x in alphaTags)

                    if not job.resolution:
                        job.resolution = re.findall('\d+x\d+', err.decode('ascii'))[0]
                        self.new_signal2.emit(job, 5, job.resolution)

                    if not alpha:
                        job.alpha = False
                        break
                    else:
                        job.alpha = True

                    correctFormat = ("Video: %s" % job.ffmpegName) in err.decode('ascii')
                    if not correctFormat:
                        job.validFormat = False
                        break
                    else:
                        job.validFormat = True

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

    def scanFolderForSequences(self):
        for folder in self.folders:
            folder.content = [x for x in os.listdir(folder.path) if (x.lower().endswith('.tga') or x.lower().endswith('.png'))]

            #check folder's internal structure for individual image prefixes
            for file in folder.content:
                numbers = re.findall('\d+', file)
                if numbers:
                    numSuffix = numbers[-1]
                    numSuffixIdx = file.rfind(numSuffix)
                    file = file[:numSuffixIdx] + str(len(numSuffix)) + file[numSuffixIdx + len(numSuffix):]
                    folder.prefixesFound.append((file, numSuffixIdx))

            folder.prefixesFound = set(folder.prefixesFound)

            #check each of the prefixes for sequence
            for prefix in folder.prefixesFound:
                matrix = prefix[0][:prefix[1]]
                list = [file for file in folder.content if file.startswith(matrix)]
                newMatrix = (matrix + '%d0' + prefix[0][prefix[1]:])
                gaps = False
                if len(list) >= 2:
                    for i in range(1, len(list)):
                        if int(re.findall('\d+', list[i])[-1]) - int(re.findall('\d+', list[i-1])[-1]) != 1:
                            gaps = True
                            break
                        else:
                            continue

                    folder.jobs.append(Sequence(folder.path, list, newMatrix, gaps))

                else:
                    folder.jobs.append(Still(os.path.join(folder.path, list[0])))

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

