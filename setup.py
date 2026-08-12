# ---------------------------------------------------------------------------
# Build shim for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2026 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import os
import subprocess
import sys
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithGrpcStubs(build_py):
    """Generate gRPC stubs before the standard build_py step.

    PYTHONNOUSERSITE=1 prevents ~/.local from leaking into the stub
    generator so that:
    - system/Debian builds: system grpcio + protobuf 4.x → old-style stubs
    - venv/uv builds: venv grpcio + protobuf 5.x/6.x → new-style stubs
    (PYTHONNOUSERSITE only blocks user site-packages, not the active venv)
    """

    def run(self):
        env = os.environ.copy()
        env['PYTHONNOUSERSITE'] = '1'
        subprocess.check_call(
            [sys.executable, 'scripts/generate-grpc-stubs.py', '--force'],
            env=env,
        )
        super().run()


setup(cmdclass={'build_py': BuildWithGrpcStubs})
