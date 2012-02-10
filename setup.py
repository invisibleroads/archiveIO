'Setup script for archiveIO'
import os

from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()


setup(
    name='archiveIO',
    version='0.4.1',
    description='Convenience decorators for reading and writing to compressed archives',
    long_description=README + '\n\n' +  CHANGES,
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='zip tar.gz tar.bz2 tar',
    author='Roy Hyunjin Han',
    author_email='starsareblueandfaraway@gmail.com',
    url='https://github.com/invisibleroads/archiveIO',
    install_requires=['decorator'],
    packages=find_packages(),
    include_package_data=True,
    test_suite='archiveIO.tests',
    tests_require=['nose'],
    zip_safe=True)
