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

    @archiveIO.save
    def save(targetPath, content):
        'Example save function'
        open(targetPath, 'wt').write(content)
        # archiveIO.save() will compress everything in the folder containing targetPath
        backupPath = os.path.join(os.path.dirname(targetPath), 'backup.txt')
        open(backupPath, 'wt').write(content)

    @archiveIO.load
    def load(sourcePath):
        'Example load function'
        content = open(sourcePath, 'rt').read()
        # archiveIO.load() will extract the archive to a folder and run the function on each file in the folder
        if os.path.basename(sourcePath) == 'backup.txt': raise IOError
        backupPath = os.path.join(os.path.dirname(sourcePath), 'backup.txt')
        assert open(backupPath, 'rt').read() == content
        return content

    data = 'xxx'
    save('sample.txt', data)
    save('sample.txt.zip', data)
    save('sample.txt.tar.gz', data)
    save('sample.txt.tar.bz2', data)
    save('sample.tar', data)
    assert load('sample.txt') == data
    assert load('sample.txt.zip') == data
    assert load('sample.txt.tar.gz') == data
    assert load('sample.txt.tar.bz2') == data
    assert load('sample.txt.tar') == data
