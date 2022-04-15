#!/usr/bin/python
# ---------------------------------------------------------------------------
# Setup script for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

from setuptools import setup, find_packages

from mtda import __version__

setup(
    name='mtda',
    version=__version__,
    scripts=['mtda-cli', 'mtda-systemd-helper', 'mtda-ui', 'mtda-config'],
    packages=find_packages(exclude=["demos"]),
    package_data={'mtda': ['assets/*.*', 'templates/*.html']},
    author='Cedric Hombourger',
    author_email='cedric.hombourger@siemens.com',

    maintainer='Cedric Hombourger',
    maintainer_email='cedric.hombourger@siemens.com',

    description='Multi-Tenant Device Access',
    long_description='''
mtda is a small agent abstracting hardware controls and interfaces for a
connected test device. The main purpose of this tool is to allow developers
and testers to remotely access and control hardware devices.
''',
    url='https://github.com/siemens/mtda',
    license='MIT',
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
        "docker",
        "flask_socketio",
        "gevent",
        "gevent-websocket",
        "kconfiglib",
        "pyserial>=2.6",
        "python-daemon>=2.0",
        "pyusb>=1.0",
        "pyzmq>=15.0,<23.0.0",
        "psutil",
        "requests",
        "urwid",
        "zerorpc>=0.6.0",
        "zstandard>=0.14",
        "zeroconf>=0.28.6"
    ],
)
