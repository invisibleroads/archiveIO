'Tests for archiveIO'
import os
from glob import glob
from cStringIO import StringIO
from shutil import rmtree
from unittest import TestCase

from archiveIO import Archive, ArchiveError, save, load, walk_paths, EXTENSION_PACKS


EXTENSIONS = [x[0] for x in EXTENSION_PACKS]
EXAMPLE_TEXT = 'xxx'
SOURCE_FOLDER = 'archiveIO/'
SOURCE_SUBFOLDER = os.path.join(SOURCE_FOLDER, 'xxx')
TARGET_NAME = 'example'
TARGET_FOLDER = TARGET_NAME + '/'


class TestArchiveIO(TestCase):

    def tearDown(self):
        try:
            os.rmdir(SOURCE_SUBFOLDER)
        except OSError:
            pass
        for path in glob(TARGET_NAME + '*'):
            if os.path.isdir(path):
                rmtree(path)
            else:
                os.remove(path)

    def test_class(self):
        os.mkdir(SOURCE_SUBFOLDER) # Make an empty subfolder
        for extension in EXTENSIONS:
            for path in TARGET_NAME + extension, StringIO():
                archive = Archive(path, extension=extension)
                archive.save(SOURCE_FOLDER)
                self.assertEqual(
                    set(os.path.abspath(TARGET_FOLDER + x) for x in walk_paths(SOURCE_FOLDER)),
                    set(os.path.abspath(x) for x in archive.load(TARGET_FOLDER)))
        archive = Archive(TARGET_NAME + EXTENSIONS[0])
        archive.save(glob(SOURCE_FOLDER + '*')[0])
        self.assertRaises(ArchiveError, Archive, TARGET_NAME, '.xxx')
        self.assertRaises(ArchiveError, Archive, StringIO())
        self.assertRaises(ArchiveError, Archive, TARGET_NAME + '.xxx')

    def test_decorators(self):
        @save
        def save_(targetPath, **kw):
            open(targetPath, 'wt').write(EXAMPLE_TEXT)
        @load
        def load_(sourcePath, **kw):
            if sourcePath.endswith('.ini'):
                raise Exception
            return open(sourcePath, 'rt').read()
        for targetPath in TARGET_NAME + '.txt', TARGET_NAME + '.zip':
            save_(targetPath)
            self.assertEqual(EXAMPLE_TEXT, load_(targetPath))
        # Save to a file-like object
        self.assertRaises(ArchiveError, save_, StringIO(), targetExtension='.zip')
        save_(StringIO(), targetName=TARGET_NAME, targetExtension='.zip')
        # Test load failure
        targetPath = TARGET_NAME + '.ini.tar.gz'
        save_(targetPath)
        self.assertRaises(IOError, load_, targetPath)
