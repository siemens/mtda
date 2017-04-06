#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

VERSION = '0.1'

setup(
    name='mtda',
    version=VERSION,
    scripts=['mtda.py'],
    packages=find_packages(),
    author='Cedric Hombourger',
    author_email='Cedric_Hombourger@mentor.com',

    maintainer='Cedric Hombourger',
    maintainer_email='Cedric_Hombourger@mentor.com',

    description='Mentor Test Device Agent',
    long_description='''
mtda is a small agent abstracting hardware controls and interfaces for a
connected test device. The main purpose of this tool is to allow developers
and testers to remotely access and control hardware devices.
''',
    url='https://stash.alm.mentorg.com/projects/PSP/repos/mtda',
    license='TBD',
    keywords='remote test',
    classifiers=[
        "Topic :: Utilities",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.0",
        "Topic :: Software Development :: Embedded Systems",
    ],

    install_requires=[
        "pyserial>=2.6",
        "python-daemon>=2.0",
        "pyusb>=1.0",
        "pyzmq>=15.0",
        "zerorpc>=0.6.0"
    ],
)
