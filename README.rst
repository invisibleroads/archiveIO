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
    from cStringIO import StringIO

    @archiveIO.save
    def save(targetPath):
        open(targetPath, 'wt').write('xxx')

    @archiveIO.load
    def load(sourcePath):
        return open(sourcePath, 'rt').read()

    save('sample.txt')
    save('sample.txt.zip')
    save('sample.txt.tar.gz')
    save('sample.txt.tar.bz2')
    save('sample.txt.tar')
    assert 'xxx' == load('sample.txt')
    assert 'xxx' == load('sample.txt.zip')
    assert 'xxx' == load('sample.txt.tar.gz')
    assert 'xxx' == load('sample.txt.tar.bz2')
    assert 'xxx' == load('sample.txt.tar')

    archive = archiveIO.Archive(StringIO(), '.tar.gz')
    archive.save([
        'sample.txt',
        'sample.txt.zip',
    ])
    with archiveIO.TemporaryFolder() as temporaryFolder:
        for filePath in archive.load(temporaryFolder):
            print filePath
