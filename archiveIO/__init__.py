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
    targetPathLower = targetPath.lower()
    # Try to recognize the extension,
    for extension, make_consumer, make_generator in extensionPacks:
        # If we have a matching extension,
        if targetPathLower.endswith(extension):
            break
    # If we did not recognize the extension,
    else:
        # Run function as usual
        return function(*args, **kwargs)
    # Remove matching extension from filename
    targetName = os.path.basename(targetPath[:targetPathLower.rfind(extension)])
    # Make temporaryFolder
    with TemporaryFolder() as temporaryFolder:
        # Run function in temporaryFolder
        temporaryPath = os.path.join(temporaryFolder, targetName)
        function(temporaryPath, *args[1:], **kwargs)
        # Enter consumer
        consumer = make_consumer(targetPath)
        consumer.next()
        # Walk function output
        for rootPath, directories, fileNames in os.walk(temporaryFolder):
            # For each file,
            for fileName in fileNames:
                filePath = os.path.join(rootPath, fileName)
                relativePath = filePath[len(temporaryFolder) + 1:]
                consumer.send((filePath, relativePath))
        # Exit consumer
        consumer.close()
    # Return
    return targetPath


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
    sourcePathLower = sourcePath.lower()
    # Try to recognize the extension,
    for extension, make_consumer, make_generator in extensionPacks:
        # If we have a matching extension,
        if sourcePathLower.endswith(extension):
            break
    # If we did not recognize the extension,
    else:
        # Run function as usual
        return function(*args, **kwargs)
    # Make temporaryFolder
    with TemporaryFolder() as temporaryFolder:
        # For each relativePath,
        for filePath in make_generator(sourcePath, temporaryFolder):
            # Run function and exit if successful
            errors = []
            try:
                return function(filePath, *args[1:], **kwargs)
            except Exception, error:
                errors.append(str(error))
        else:
            raise IOError('Could not run %s on any file in %s:\n%s' % (function, sourcePath, '\n'.join(errors)))


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
