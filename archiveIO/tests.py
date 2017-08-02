'Tests for archiveIO'
import os
from glob import glob
from shutil import rmtree
from six import BytesIO
from unittest import TestCase

from archiveIO import (
    Archive, ArchiveError, save, load, select_extensions, walk_paths,
    EXTENSION_PACKS)


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

    def test_class_works(self):
        os.mkdir(SOURCE_SUBFOLDER)  # Make an empty subfolder
        for extension in EXTENSIONS:
            for path in TARGET_NAME + extension, BytesIO():
                archive = Archive(path, extension=extension)
                archive.save(SOURCE_FOLDER)
                self.assertEqual(
                    set(os.path.abspath(
                        TARGET_FOLDER + x) for x in walk_paths(SOURCE_FOLDER)),
                    set(os.path.abspath(
                        x) for x in archive.load(TARGET_FOLDER)))
        archive = Archive(TARGET_NAME + EXTENSIONS[0])
        archive.save(glob(SOURCE_FOLDER + '*')[0])
        archive.save(glob(SOURCE_FOLDER + '*'))
        self.assertRaises(ArchiveError, Archive, TARGET_NAME, '.xxx')
        self.assertRaises(ArchiveError, Archive, BytesIO())
        self.assertRaises(ArchiveError, Archive, TARGET_NAME + '.xxx')

    def test_decorators_work(self):

        @save
        def save_(targetPath, **kw):
            open(targetPath, 'wt').write(EXAMPLE_TEXT)

        @load
        def load_(sourcePath, **kw):
            return open(sourcePath, 'rt').read()

        for targetPath in TARGET_NAME + '.txt', TARGET_NAME + '.zip':
            save_(targetPath)
            self.assertEqual(EXAMPLE_TEXT, load_(targetPath))
        # Save to a file-like object
        self.assertRaises(
            ArchiveError, save_, BytesIO(), targetExtension='.zip')
        save_(
            BytesIO(), targetName=TARGET_NAME, targetExtension='.zip')

    def test_select_extensions(self):
        'Select file extensions'
        self.assertEqual(
            ['a.csv', 'b.csv', 'a.txt', 'b.txt'],
            select_extensions(['a.csv', 'a.txt', 'b.csv', 'b.txt'], [
                '.csv', '.txt']))
        targetPath = TARGET_NAME + '.zip'

        @save
        def save_(targetPath, **kw):
            open((targetPath + '.txt'), 'wt')
            open((targetPath + '.csv'), 'wt')
        save_(targetPath)

        @load(extensions=['.xxx', '.txt'])
        def load_(sourcePath, **kw):
            return sourcePath
        self.assertEqual('.txt', os.path.splitext(load_(targetPath))[1])

        @load(extensions=['.csv', '.txt'])
        def load_(sourcePath, **kw):
            return sourcePath
        self.assertEqual('.csv', os.path.splitext(load_(targetPath))[1])

    def test_raise_exception(self):

        @save
        def save_(targetPath, **kw):
            open(targetPath, 'wt').write(EXAMPLE_TEXT)

        @load(CustomException=SystemError)
        def load_(sourcePath, **kw):
            if sourcePath.endswith('.ini'):
                raise Exception
            return open(sourcePath, 'rt').read()

        # Test open failure
        targetPath = TARGET_NAME + '.empty.tar.gz'
        open(targetPath, 'wb')
        self.assertRaises(SystemError, load_, targetPath)
        # Test load failure
        targetPath = TARGET_NAME + '.ini.tar.gz'
        save_(targetPath)
        self.assertRaises(SystemError, load_, targetPath)
