'Convenience decorators for reading and writing to compressed archives'
import os
import shutil
import zipfile
import tarfile
import tempfile
from decorator import decorator


class Archive(object):
    
    def __init__(self, path, extension=None):
        """
        The path can be a string or file-like object.
        The extension determines the archive format.
        """
        # If the extension is specified, use it
        if extension:
            try:
                make_consumer, make_generator = dict(EXTENSION_PACKS)[extension.lower()]
            except KeyError:
                raise ArchiveError('Could not recognize file extension: %s' % extension)
        # If path is a file-like object, raise Exception
        elif hasattr(path, 'read'):
            raise ArchiveError('Must specify file extension when using a file-like object')
        # If path is a string, try to recognize the extension
        else:
            pathLower = path.lower()
            for extension, (make_consumer, make_generator) in EXTENSION_PACKS:
                if pathLower.endswith(extension):
                    break
            else:
                raise ArchiveError('Could not recognize archive format from file extension')
        # Set
        self.__path = path
        self.__extension = extension
        self.__make_consumer = make_consumer
        self.__make_generator = make_generator

    def save(self, filePaths, basePath=''):
        """
        Compress filePaths using the extension specified in archivePath,
        truncating each filePath into a relativePath using basePath.
        """
        # Convert filePaths into a list if it isn't one already
        if not hasattr(filePaths, '__iter__'):
            filePaths = [filePaths]
        if basePath:
            baseIndex = len(os.path.abspath(basePath)) + 1
            truncate_basePath = lambda x: os.path.abspath(x)[baseIndex:]
        else:
            truncate_basePath = lambda x: x
        consumer = self.__make_consumer(self.__path)
        consumer.next()
        for filePath in expand_paths(filePaths):
            relativePath = truncate_basePath(filePath)
            consumer.send((filePath, relativePath))
        consumer.close()
        # If path is a file-like object, prepare it
        if hasattr(self.__path, 'read'):
            self.__path.reset()
        return self.__path

    def load(self, targetFolder):
        'Uncompress archivePath to a targetFolder.'
        # If path is a file-like object, prepare it
        if hasattr(self.__path, 'read'):
            self.__path.reset()
        return self.__make_generator(self.__path, targetFolder)

    def get_extension(self):
        return self.__extension


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


@decorator
def save(function, *args, **kw):
    """
    Decorator to support saving to compressed files for functions
    whose first argument is the targetPath

    If the first argument ends with a recognized extension,
    the decorator runs the function in a temporary folder and
    compresses the resulting output to targetPath.

    Archive format is determined by file extension:
    .zip .tar.gz .tar.bz2 .tar
    """
    targetPath = kw.get('targetPath', args[0])
    try:
        archive = Archive(targetPath, extension=kw.get('targetExtension'))
    # If we did not recognize the extension, run function as usual
    except ArchiveError:
        return function(*args, **kw)
    targetName = kw.get('targetName')
    if not targetName:
        # If path is a file-like object, raise exception
        if hasattr(targetPath, 'read'):
            raise ArchiveError('Must specify targetName when using a file-like object')
        # If path is a string, remove matching extension from filename
        else:
            targetName = os.path.basename(targetPath[:targetPath.lower().rfind(archive.get_extension())])
    # Make temporaryFolder
    with TemporaryFolder() as temporaryFolder:
        # Run function in temporaryFolder
        function(os.path.join(temporaryFolder, targetName), *args[1:], **kw)
        # Save
        return archive.save(temporaryFolder, temporaryFolder)


@decorator
def load(function, *args, **kw):
    """
    Decorator to support loading from compressed files for functions
    whose first argument is the sourcePath

    If the first argument ends with a recognized extension,
    the decorator uncompresses sourcePath to a temporary folder
    and runs the function on each resulting file until it succeeds.

    Archive format is determined by file extension:
    .zip .tar.gz .tar.bz2 .tar
    """
    sourcePath = kw.get('sourcePath', args[0])
    try:
        archive = Archive(sourcePath)
    # If we did not recognize the extension, run function as usual
    except ArchiveError:
        return function(*args, **kw)
    # Make temporaryFolder
    with TemporaryFolder() as temporaryFolder:
        errors = []
        # For each uncompressed filePath,
        for filePath in archive.load(temporaryFolder):
            # Run function and exit if successful
            try:
                return function(filePath, *args[1:], **kw)
            except Exception, error:
                errors.append(str(error))
        else:
            raise IOError('Could not run %s on any file in %s:\n%s' % (function, sourcePath, '\n'.join(errors)))


def expand_paths(paths):
    'Expand folderPaths'
    filePaths = []
    for path in paths:
        if os.path.isdir(path):
            filePaths.extend(walk_paths(path))
        elif os.path.exists(path):
            filePaths.append(path)
    return set(filePaths)


def walk_paths(path):
    'Yield filePaths one by one from the specified path'
    path = os.path.abspath(path)
    for rootPath, folderNames, fileNames in os.walk(path):
        for fileName in fileNames:
            yield os.path.join(rootPath, fileName)
        if not folderNames and not fileNames and os.path.abspath(rootPath) != path:
            yield rootPath


def open_tarfile(targetPath, mode):
    valueByKey = dict(mode=mode)
    if hasattr(targetPath, 'read'):
        valueByKey['fileobj'] = targetPath
    else:
        valueByKey['name'] = targetPath
    return tarfile.open(**valueByKey)


def make_consumer_tar(targetPath, mode='w'):
    'Save .tar file'
    def filter_(tarInfo):
        'Anonymize file data'
        tarInfo.uid = tarInfo.gid = 0
        tarInfo.uname = tarInfo.gname = 'root'
        return tarInfo
    with open_tarfile(targetPath, mode) as targetFile:
        while True:
            filePath, relativePath = yield
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
            filePath, relativePath = yield
            targetFile.write(filePath, relativePath)


def make_generator_tar(sourcePath, temporaryFolder):
    'Load .tar.gz or .tar.bz2 or .tar file'
    with open_tarfile(sourcePath, 'r') as sourceFile:
        sourceFile.extractall(temporaryFolder)
        for relativePath in sourceFile.getnames():
            yield os.path.join(temporaryFolder, relativePath)


def make_generator_zip(sourcePath, temporaryFolder):
    'Load .zip file'
    with zipfile.ZipFile(sourcePath) as sourceFile:
        sourceFile.extractall(temporaryFolder)
        for relativePath in sourceFile.namelist():
            yield os.path.join(temporaryFolder, relativePath)


EXTENSION_PACKS = [
    ('.zip', (make_consumer_zip, make_generator_zip)),
    ('.tar.gz', (make_consumer_tar_gz, make_generator_tar)),
    ('.tar.bz2', (make_consumer_tar_bz2, make_generator_tar)),
    ('.tar', (make_consumer_tar, make_generator_tar)),
]
