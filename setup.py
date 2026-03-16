#!/usr/bin/python
# ---------------------------------------------------------------------------
# Setup script for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2026 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist
import os
import re
import subprocess
import sys


def _generate_grpc_stubs():
    """Run protoc and fix the generated stub import for package usage.

    grpc_tools emits a bare ``import mtda_pb2`` in mtda_pb2_grpc.py.
    That works when both files sit in the same directory on sys.path, but
    breaks when they live inside the ``mtda.grpc`` package.  We rewrite
    the import to an absolute package import after generation.

    If the stubs already exist (e.g. in an unpacked sdist or Debian source
    package) we skip protoc so that grpcio-tools is not required at build
    time in environments that don't have it installed.
    """
    grpc_stub = 'mtda/grpc/mtda_pb2_grpc.py'
    if os.path.exists(grpc_stub):
        return
    subprocess.check_call([
        sys.executable, '-m', 'grpc_tools.protoc',
        '-I', 'mtda/grpc',
        '--python_out=mtda/grpc',
        '--grpc_python_out=mtda/grpc',
        'mtda/grpc/mtda.proto',
    ])
    with open(grpc_stub, 'r') as f:
        src = f.read()
    src = src.replace(
        'import mtda_pb2 as mtda__pb2',
        'from mtda.grpc import mtda_pb2 as mtda__pb2',
    )
    with open(grpc_stub, 'w') as f:
        f.write(src)


class BuildPyWithProto(build_py):
    """Regenerate gRPC stubs from mtda/grpc/mtda.proto before building."""

    def run(self):
        _generate_grpc_stubs()
        super().run()


class SdistWithProto(sdist):
    """Regenerate gRPC stubs before creating the source distribution.

    This ensures the stubs are present in the sdist tarball so that the
    package can be imported directly from an unpacked sdist (e.g. when
    tox runs the test scripts against the source tree).
    """

    def run(self):
        _generate_grpc_stubs()
        super().run()


# Read version without importing the package (safe in isolated build envs).
with open('mtda/__version__.py') as _f:
    __version__ = re.search(
        r"^__version__\s*=\s*'([^']+)'", _f.read(), re.M
    ).group(1)

setup(
    name='mtda',
    version=__version__,
    cmdclass={
        'build_py': BuildPyWithProto,
        'sdist': SdistWithProto,
    },
    scripts=[
        'mtda-cli',
        'mtda-service',
        'mtda-systemd-helper',
        'mtda-www'
    ],
    packages=find_packages(exclude=["demos"]),
    package_data={'mtda': ['assets/*.*', 'templates/*.html',
                           'grpc/*.proto', 'grpc/*_pb2*.py']},
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

    include_package_data=True,

    install_requires=[
        "docker",
        "gevent",
        "netifaces>=0.11.0",
        "pyserial>=2.6",
        "python-daemon>=2.0",
        "grpcio>=1.51",
        "grpcio-tools>=1.51",
        "pyusb>=1.0",
        "psutil",
        "requests",
        "systemd-python>=234",
        "tornado",
        "zstandard>=0.14",
        "zeroconf>=0.28.6"
    ],
)
