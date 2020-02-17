# -*- coding: utf-8 -*-
import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='autotable-YoRyan',
    version='0.0.1',
    author='Ryan Young',
    author_email='ryan@youngryan.com',
    description='An Open Rails timetable generator that uses GTFS data',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/YoRyan/autotable',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    install_requires=[
        'gtfs_kit',
        'more-itertools',
        #'pandas',
        'pyproj',
        'pyyaml',
        'requests',
    ],
    entry_points={
        'console_scripts': ['autotable=autotable.main:main'],
    },
)