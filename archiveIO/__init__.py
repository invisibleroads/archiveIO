'Convenience decorators for reading and writing to compressed archives'
import os
import shutil
import zipfile
import tarfile
import tempfile
from decorator import decorator


@decorator
def save(function, *args, **kwargs):
    """
    Decorator to support saving to compressed files for functions
    whose first argument is the targetPath

    If the first argument ends with a recognized extension,
    the decorator runs the function in a temporary folder and
    compresses the resulting output to targetPath.

    Archive format is determined by file extension:
    .zip .tar.gz .tar.bz2 .tar
    """
    targetPath = kwargs.get('targetPath', args[0])
    try:
        archive = Archive(targetPath)
    # If we did not recognize the extension, run function as usual
    except ArchiveError:
        return function(*args, **kwargs)
    # Make temporaryFolder
    with TemporaryFolder() as temporaryFolder:
        # Run function in temporaryFolder
        temporaryPath = os.path.join(temporaryFolder, archive.getName())
        function(temporaryPath, *args[1:], **kwargs)
        filePaths = []
        # Walk function output
        for rootPath, directories, fileNames in os.walk(temporaryFolder):
            # For each file,
            for fileName in fileNames:
                filePaths.append(os.path.join(rootPath, fileName))
        # Save
        return archive.save(filePaths, temporaryFolder)


@decorator
def load(function, *args, **kwargs):
    """
    Decorator to support loading from compressed files for functions
    whose first argument is the sourcePath

    If the first argument ends with a recognized extension,
    the decorator uncompresses sourcePath to a temporary folder
    and runs the function on each resulting file until it succeeds.

    Archive format is determined by file extension:
    .zip .tar.gz .tar.bz2 .tar
    """
    sourcePath = kwargs.get('sourcePath', args[0])
    try:
        archive = Archive(sourcePath)
    # If we did not recognize the extension, run function as usual
    except ArchiveError:
        return function(*args, **kwargs)
    # Make temporaryFolder
    with TemporaryFolder() as temporaryFolder:
        # For each uncompressed filePath,
        for filePath in archive.load(temporaryFolder):
            # Run function and exit if successful
            errors = []
            try:
                return function(filePath, *args[1:], **kwargs)
            except Exception, error:
                errors.append(str(error))
        else:
            raise IOError('Could not run %s on any file in %s:\n%s' % (function, sourcePath, '\n'.join(errors)))


class Archive(object):
    'Archive processor'
    
    def __init__(self, path):
        'Prepare'
        pathLower = path.lower()
        # Try to recognize the extension,
        for extension, make_consumer, make_generator in extensionPacks:
            # If we have a matching extension, exit loop
            if pathLower.endswith(extension):
                break
        # If we did not recognize the extension, raise exception
        else:
            raise ArchiveError('Could not recognize compression format from file extension')
        # Remove matching extension from filename
        name = os.path.basename(path[:pathLower.rfind(extension)])
        # Set
        self.__path = path
        self.__make_consumer = make_consumer
        self.__make_generator = make_generator
        self.__name = name

    def save(self, filePaths, basePath=''):
        """
        Compress filePaths using the extension specified in archivePath,
        truncating each filePath into a relativePath using basePath.
        """
        # Convert filePaths into a list if it isn't one already
        if not hasattr(filePaths, '__iter__'):
            filePaths = [filePaths]
        # Enter consumer
        consumer = self.__make_consumer(self.__path)
        consumer.next()
        # For each filePath,
        for filePath in filePaths:
            # Truncate filePath into relativePath
            relativeIndex = len(basePath) + 1 if basePath else 0
            consumer.send((filePath, filePath[relativeIndex:]))
        # Exit consumer
        consumer.close()
        # Return
        return self.__path

    def load(self, targetFolder):
        'Uncompress archivePath to a targetFolder.'
        return self.__make_generator(self.__path, targetFolder)

    def getName(self):
        'Return archive filename after stripping file extension'
        return self.__name


class ArchiveError(Exception):
    'Custom exception for archiveIO'
    pass


class TemporaryFolder(object):
    'Context manager that creates a temporary folder on entry and removes it on exit'

    def __init__(self, suffix='', prefix='tmp', dir=None):
        self.suffix = suffix
        self.prefix = prefix
        self.dir = dir

    def __enter__(self):
        self.temporaryFolder = tempfile.mkdtemp(self.suffix, self.prefix, self.dir)
        return self.temporaryFolder

    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.temporaryFolder)


def make_consumer_tar(targetPath, mode='w'):
    'Save .tar file'
    def filter_(tarInfo):
        'Anonymize file data'
        tarInfo.uid = tarInfo.gid = 0
        tarInfo.uname = tarInfo.gname = 'root'
        return tarInfo
    with tarfile.open(targetPath, mode) as targetFile:
        while True:
            filePath, relativePath = (yield)
            targetFile.add(filePath, relativePath, recursive=False, filter=filter_)


def make_consumer_tar_gz(targetPath):
    'Save .tar.gz file'
    return make_consumer_tar(targetPath, mode='w:gz')


def make_consumer_tar_bz2(targetPath):
    'Save .tar.bz2 file'
    return make_consumer_tar(targetPath, mode='w:bz2')


def make_consumer_zip(targetPath):
    'Save .zip file'
    with zipfile.ZipFile(targetPath, 'w', zipfile.ZIP_DEFLATED) as targetFile:
        while True:
            filePath, relativePath = (yield)
            targetFile.write(filePath, relativePath)


def make_generator_tar(sourcePath, temporaryFolder):
    'Load .tar.gz or .tar.bz2 or .tar file'
    with tarfile.open(sourcePath, 'r') as sourceFile:
        sourceFile.extractall(temporaryFolder)
        for relativePath in sourceFile.getnames():
            yield os.path.join(temporaryFolder, relativePath)


def make_generator_zip(sourcePath, temporaryFolder):
    'Load .zip file'
    with zipfile.ZipFile(sourcePath) as sourceFile:
        sourceFile.extractall(temporaryFolder)
        for relativePath in sourceFile.namelist():
            yield os.path.join(temporaryFolder, relativePath)


extensionPacks = [
    ('.zip', make_consumer_zip, make_generator_zip),
    ('.tar.gz', make_consumer_tar_gz, make_generator_tar),
    ('.tar.bz2', make_consumer_tar_bz2, make_generator_tar),
    ('.tar', make_consumer_tar, make_generator_tar),
]
