# ---------------------------------------------------------------------------
# Utility classes/functions
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2026 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import os
import psutil
import re
import signal
import threading
import time
import mtda.constants as CONSTS


class SafeXml:
    @staticmethod
    def fromstring(data):
        """Parse XML from a string like xml.etree.ElementTree.fromstring(),
        but reject any DOCTYPE declaration. Since custom (and hence
        recursively expandable, "billion laughs" style) entities can only
        be declared from a DOCTYPE's internal subset, refusing any DOCTYPE
        outright prevents entity-expansion denial-of-service without
        needing an extra dependency (e.g. defusedxml)."""
        import xml.parsers.expat
        from xml.etree.ElementTree import TreeBuilder, ParseError

        builder = TreeBuilder()
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = builder.start
        parser.EndElementHandler = builder.end
        parser.CharacterDataHandler = builder.data

        def _forbid_doctype(name, pubid, sysid, has_internal_subset):
            raise ParseError("XML DOCTYPE declarations are not allowed")

        parser.StartDoctypeDeclHandler = _forbid_doctype

        if isinstance(data, str):
            data = data.encode("utf-8")
        parser.Parse(data, True)
        return builder.close()


class BmapUtils:
    def parseBmap(bmap, bmap_path):
        try:
            bmapDict = {}
            bmapDict["BlockSize"] = int(
                bmap.find("BlockSize").text.strip())
            bmapDict["BlocksCount"] = int(
                bmap.find("BlocksCount").text.strip())
            bmapDict["MappedBlocksCount"] = int(
                bmap.find("MappedBlocksCount").text.strip())
            bmapDict["ImageSize"] = int(
                bmap.find("ImageSize").text.strip())
            bmapDict["ChecksumType"] = \
                bmap.find("ChecksumType").text.strip()
            bmapDict["BmapFileChecksum"] = \
                bmap.find("BmapFileChecksum").text.strip()
            bmapDict["BlockMap"] = []
            for child in bmap.find("BlockMap").findall("Range"):
                range = child.text.strip().split("-")
                first = range[0]
                last = range[0] if len(range) == 1 else range[1]
                bmapDict["BlockMap"].append({
                    "first": int(first),
                    "last": int(last),
                    "chksum": child.attrib["chksum"]
                })
        except Exception:
            print(f"Error parsing '{bmap_path}', probably not a bmap 2.0 file")
            return None
        return bmapDict


class Compression:
    def from_extension(path):
        if path.endswith(".bz2"):
            result = CONSTS.IMAGE.BZ2.value
        elif path.endswith(".gz"):
            result = CONSTS.IMAGE.GZ.value
        elif path.endswith(".zst"):
            result = CONSTS.IMAGE.ZST.value
        elif path.endswith(".xz"):
            result = CONSTS.IMAGE.XZ.value
        else:
            result = CONSTS.IMAGE.RAW.value
        return result


class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class Size:
    @staticmethod
    def to_bytes(value, default_suffix: str = "") -> int:
        """
        Convert strings like '10K', '5MB', '2GiB', '42'
        """

        if isinstance(value, (int, float)):
            value = str(value)
        value = value.strip()

        m = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]*)", value)
        if not m:
            raise ValueError(f"Invalid size format: {value}")

        number, suffix = m.groups()
        number = float(number)
        if not suffix and default_suffix:
            suffix = default_suffix

        suffix = suffix.upper()
        MULTIPLIERS = {
            "":     1,
            "B":    1,
            "K":    1000,
            "KB":   1000,
            "M":    1000**2,
            "MB":   1000**2,
            "G":    1000**3,
            "GB":   1000**3,
            "KIB":  1024,
            "MIB":  1024**2,
            "GIB":  1024**3,
        }

        if suffix not in MULTIPLIERS:
            raise ValueError(f"Unknown size suffix: '{suffix}'")
        return int(number * MULTIPLIERS[suffix])


class System():
    def kill(name, pid, timeout=3):
        pid = int(pid)
        tries = timeout
        if psutil.pid_exists(pid):
            os.kill(pid, signal.SIGTERM)
        while tries > 0 and psutil.pid_exists(pid):
            time.sleep(1)
            tries = tries - 1
        if psutil.pid_exists(pid):
            os.kill(pid, signal.SIGKILL)
        return psutil.pid_exists(pid)


class SystemdDeviceUnit():
    def create_device_dependency(dropin_path: str, device_path: str):
        """
        Create a systemd drop-in file to wait for a specific device
        to become available.
        """
        # escape device name according to systemd.unit requirements
        device = device_path[1:].replace('-', '\\x2d').replace('/', '-')
        with open(dropin_path, 'w') as f:
            f.write('[Unit]\n')
            f.write(f'Wants={device}.device\n')
            f.write(f'After={device}.device\n')
