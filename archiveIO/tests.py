'Tests for archiveIO'
import os

import archiveIO


sampleName = 'sample.txt'
sampleText = '0123456789'


@archiveIO.save
def save(targetPath, content):
    assert os.path.basename(targetPath) == sampleName
    open(targetPath, 'wt').write(content)
    backupPath = os.path.join(os.path.dirname(targetPath), 'backup.txt')
    open(backupPath, 'wt').write(content)


@archiveIO.load
def load(sourcePath):
    content = open(sourcePath, 'rt').read()
    if os.path.basename(sourcePath) == 'backup.txt':
        raise IOError
    backupPath = os.path.join(os.path.dirname(sourcePath), 'backup.txt')
    assert open(backupPath, 'rt').read() == content
    return content


@archiveIO.load
def load_(sourcePath):
    raise Exception


def test():
    with archiveIO.TemporaryFolder() as temporaryFolder:
        # Test each extension
        for extension in [''] + [x[0] for x in archiveIO.extensionPacks]:
            archivePath = os.path.join(temporaryFolder, sampleName + extension)
            save(archivePath, sampleText)
            assert load(archivePath) == sampleText
        # Test case when loading fails for each file in an archive
        try:
            load_(archivePath)
            raise AssertionError
        except IOError:
            pass
