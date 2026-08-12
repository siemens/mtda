#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# gRPC Stub Generator for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2026 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

"""
Generate gRPC stubs from mtda.proto and fix imports for package usage.

This script:
1. Runs protoc to generate Python stubs from mtda/grpc/mtda.proto
2. Fixes the import statement in mtda_pb2_grpc.py to use absolute package imports

Stubs are generated using the active Python interpreter so they match
the protobuf version in the calling environment:
  - uv/venv: uses the venv's grpcio-tools + protobuf (new-style stubs)
  - Debian build: uses system grpcio + protobuf 4.x (old-style stubs)

Usage:
    python scripts/generate-grpc-stubs.py [--force]

Options:
    --force    Regenerate stubs even if they already exist
"""

import argparse
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(
        description='Generate gRPC stubs for MTDA'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Regenerate stubs even if they already exist'
    )
    args = parser.parse_args()

    # Define paths
    proto_file = 'mtda/grpc/mtda.proto'
    grpc_stub = 'mtda/grpc/mtda_pb2_grpc.py'
    pb2_stub = 'mtda/grpc/mtda_pb2.py'

    # Check if stubs already exist
    if not args.force and os.path.exists(grpc_stub) and os.path.exists(pb2_stub):
        print(f"gRPC stubs already exist at {grpc_stub} and {pb2_stub}")
        print("Use --force to regenerate")
        return 0

    # Check if proto file exists
    if not os.path.exists(proto_file):
        print(f"Error: Proto file not found at {proto_file}", file=sys.stderr)
        return 1

    print(f"Generating gRPC stubs from {proto_file}...")

    try:
        subprocess.check_call([
            sys.executable, '-m', 'grpc_tools.protoc',
            '-I', 'mtda/grpc',
            '--python_out=mtda/grpc',
            '--grpc_python_out=mtda/grpc',
            proto_file,
        ])
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to run protoc: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("Error: grpc_tools not found.", file=sys.stderr)
        print("Install: sudo apt install python3-grpcio", file=sys.stderr)
        return 1

    # Fix import in mtda_pb2_grpc.py
    print(f"Fixing imports in {grpc_stub}...")
    try:
        with open(grpc_stub, 'r') as f:
            content = f.read()

        # Replace bare import with package import
        content = content.replace(
            'import mtda_pb2 as mtda__pb2',
            'from mtda.grpc import mtda_pb2 as mtda__pb2'
        )

        with open(grpc_stub, 'w') as f:
            f.write(content)

        print("✓ gRPC stubs generated successfully")
        print(f"  - {pb2_stub}")
        print(f"  - {grpc_stub}")
        return 0

    except Exception as e:
        print(f"Error: Failed to fix imports: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
