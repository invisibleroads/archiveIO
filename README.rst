archiveIO
=========
Here are some decorators for reading and writing to compressed archives.


Installation
------------
::

    easy_install -U archiveIO


Usage
-----
::

    import archiveIO
    import os
    from six import BytesIO

    # Define a function that generates archive contents
    @archiveIO.save
    def save(targetPath):
        open(targetPath, 'wt').write('xxx')
    # Define a function that processes archive contents
    @archiveIO.load
    def load(sourcePath):
        return open(sourcePath, 'rt').read()

    # Save archives
    save('sample.txt')
    save('sample.txt.zip')
    save('sample.txt.tar.gz')
    save('sample.txt.tar.bz2')
    save('sample.txt.tar')
    # Load archives
    assert 'xxx' == load('sample.txt')
    assert 'xxx' == load('sample.txt.zip')
    assert 'xxx' == load('sample.txt.tar.gz')
    assert 'xxx' == load('sample.txt.tar.bz2')
    assert 'xxx' == load('sample.txt.tar')

    # Create an archive containing two files
    @archiveIO.save
    def save(targetPath):
        open(targetPath + '.txt', 'wt')
        open(targetPath + '.csv', 'wt')
    targetPath = 'sample.zip'
    save(targetPath)
    # Target CSV files before TXT files
    @archiveIO.load(extensions=['.csv', '.txt'])
    def load(sourcePath):
        return os.path.basename(sourcePath)
    assert 'sample.csv' == load(targetPath)

    # Use MyException instead of IOError
    class MyException(Exception):
        pass
    @archiveIO.load(CustomException=MyException)
    def load(sourcePath):
        return sourcePath
    try:
        load('xxx.tar.gz')
    except MyException, error:
        print error

    # Compress directly into a string buffer
    archive = archiveIO.Archive(BytesIO(), '.tar.gz')
    archive.save([
        'sample.txt',
        'sample.txt.zip',
    ])
    # Uncompress into a temporary folder
    with archiveIO.TemporaryFolder() as temporaryFolder:
        for filePath in archive.load(temporaryFolder):
            print filePath
