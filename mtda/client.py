# ---------------------------------------------------------------------------
# MTDA Client
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2021 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------


import os
import random
import socket
import subprocess
import tempfile
import time
import zmq
import zstandard as zstd

from mtda.main import MultiTenantDeviceAccess
from mtda.utils import Compression
import mtda.constants as CONSTS

# Pyro
try:
    from Pyro5.compatibility import Pyro4
except ImportError:
    import Pyro4


class Client:

    def __init__(self, host=None, session=None, config_files=None,
                 timeout=CONSTS.RPC.TIMEOUT):
        """
        Client to control mtda device
        :param host:    hostname or ip of mtda device
        :param session: mtda session id
        :param config_files: configuration filenames
        :param timeout: RPC timeout in seconds
        """
        agent = MultiTenantDeviceAccess()
        agent.load_config(host, config_files=config_files)
        if agent.remote is not None:
            uri = f"PYRO:mtda.main@{agent.remote}:{agent.ctrlport}"
            Pyro4.config.SERIALIZER = "marshal"
            self._impl = Pyro4.Proxy(uri)
            self._impl._pyroTimeout = timeout
        else:
            self._impl = agent
        self._agent = agent
        self._data = None

        if session is None:
            HOST = socket.gethostname()
            USER = os.getenv("USER")
            WORDS = "/usr/share/dict/words"
            if os.path.exists(WORDS):
                WORDS = open(WORDS).read().splitlines()
                name = random.choice(WORDS)
                if name.endswith("'s"):
                    name = name.replace("'s", "")
            elif USER is not None and HOST is not None:
                name = f"{USER}@{HOST}"
            else:
                name = "mtda"
            self._session = os.getenv('MTDA_SESSION', name)
        else:
            self._session = session

    def __getattr__(self, name):
        if self._impl is None:
            return None

        attr = getattr(self._impl, name)
        if self._session and callable(attr):
            def wrapper(*args, **kwargs):
                kwargs['session'] = self._session
                return attr(*args, **kwargs)
            return wrapper
        return attr

    def console_prefix_key(self):
        return self._agent.console_prefix_key()

    def console_getkey(self):
        return self._agent.console_getkey()

    def console_init(self):
        return self._agent.console_init()

    def console_port(self):
        return self._agent.console_port()

    def console_remote(self, host, screen):
        return self._agent.console_remote(host, screen)

    def console_toggle(self):
        return self._agent.console_toggle(session=self._session)

    def debug(self, level, msg):
        if self._agent:
            return self._agent.debug(level, msg)

    def monitor_remote(self, host, screen):
        return self._agent.monitor_remote(host, screen)

    def pastebin_api_key(self):
        return self._agent.pastebin_api_key()

    def pastebin_endpoint(self):
        return self._agent.pastebin_endpoint()

    def storage_network(self, remote):
        cmd_nbd = '/usr/sbin/nbd-client'
        if os.path.exists(cmd_nbd) is False:
            raise RuntimeError(f'{cmd_nbd} not found')

        rdev = self._impl.storage_network(session=self._session)
        if rdev is None:
            raise RuntimeError('could not put storage on network')

        cmd = ['sudo', '/usr/sbin/modprobe', 'nbd']
        subprocess.check_call(cmd)

        cmd = ['sudo', cmd_nbd, '-N', 'mtda-storage', remote]
        subprocess.check_call(cmd)

    def storage_open(self, size=0, **kwargs):
        session = kwargs.get('session', self._session)
        port = self._impl.storage_open(size, session=session)
        return self._storage_socket(port)

    def _storage_socket(self, port):
        tries = 60
        while tries > 0:
            tries = tries - 1
            try:
                host = self.remote()
                context = zmq.Context()
                socket = context.socket(zmq.PUSH)
                hwm = int(
                        CONSTS.WRITER.HIGH_WATER_MARK
                        /
                        CONSTS.WRITER.READ_SIZE
                )
                socket.setsockopt(zmq.SNDHWM, hwm)
                socket.setsockopt(zmq.MAXMSGSIZE, CONSTS.WRITER.READ_SIZE)
                socket.connect(f'tcp://{host}:{port}')
                self._data = socket
                return socket
            except Exception:
                if tries > 0:
                    time.sleep(1)
                    pass
                else:
                    raise

    def storage_update(self, dest, src=None, callback=None, **kwargs):
        session = kwargs.get('session', self._session)

        path = dest if src is None else src
        st = os.stat(path)
        size = st.st_size

        port = self._impl.storage_update(dest, size, session=session)
        self._storage_socket(port)

        blksz = self._agent.blksz
        impl = self._impl

        # Get file handler from specified path
        file = ImageFile.new(path, impl, session, blksz, callback)

        try:
            # Prepare for download/copy
            file.prepare(self._data, size)

            # Copy image to shared storage
            file.copy()

            # Wait for background writes to complete
            file.flush()

        except Exception:
            raise
        finally:
            # Storage may be closed now
            self.storage_close()

    def storage_write_image(self, path, callback=None):
        blksz = self._agent.blksz
        impl = self._impl
        session = self._session

        # Get file handler from specified path
        file = ImageFile.new(path, impl, session, blksz, callback)

        # Open the shared storage device so we own it
        # It also prevents us from loading a new bmap file while
        # another transfer may be on-going
        self.storage_open(file.size)

        # Automatically discover the bmap file
        bmap = None
        image_path = file.path()
        image_size = None
        while True:
            bmap_path = image_path + '.bmap'
            try:
                bmap = file.bmap(bmap_path)
                if bmap is not None:
                    import xml.etree.ElementTree as ET

                    bmap = ET.fromstring(bmap)
                    print(f"Discovered bmap file '{bmap_path}'")
                    bmapDict = self.parseBmap(bmap, bmap_path)
                    self._impl.storage_bmap_dict(bmapDict)
                    image_size = bmapDict['ImageSize']
                    break
            except Exception:
                pass
            image_path, ext = os.path.splitext(image_path)
            if ext == "":
                print("No bmap file found at location of image")
                break

        try:
            # Prepare for download/copy
            file.prepare(self._data, image_size)

            # Copy image to shared storage
            file.copy()

            # Wait for background writes to complete
            file.flush()

        except Exception:
            raise
        finally:
            # Storage may be closed now
            self.storage_close()
            self._impl.storage_bmap_dict(None)

    def parseBmap(self, bmap, bmap_path):
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

    def start(self):
        return self._agent.start()

    def stop(self):
        if self._agent.remote is not None:
            self._impl.close()
        else:
            self._agent.stop()

    def remote(self):
        return self._agent.remote

    def session(self):
        return self._session

    def target_lock(self, retries=0):
        status = False
        while status is False:
            status = self._impl.target_lock(session=self._session)
            if retries <= 0 or status is True:
                break
            retries = retries - 1
            time.sleep(60)
        return status

    def version(self):
        return self._agent.version

    def video_url(self, host="", opts=None):
        if host == "":
            host = os.getenv("MTDA_REMOTE", "")
        return self._impl.video_url(host, opts)


class ImageFile:
    """ Base class for image files (local or remote) """

    def new(path, agent, session, blksz, callback=None):
        if path.startswith('s3:'):
            return ImageS3(path, agent, session, blksz, callback)
        else:
            return ImageLocal(path, agent, session, blksz, callback)

    def __init__(self, path, agent, session, blksz, callback=None):
        self._agent = agent
        self._blksz = blksz
        self._callback = callback
        self._imgname = os.path.basename(path)
        self._inputsize = 0
        self._path = path
        self._session = session
        self._totalread = 0
        self._totalsent = 0

    def bmap(self, path):
        return None

    def flush(self):
        # Wait for background writes to complete
        agent = self._agent
        callback = self._callback
        imgname = self._imgname
        inputsize = self._inputsize
        totalread = self._totalread
        outputsize = self._outputsize

        self._socket.send(b'')
        agent.storage_flush(self._totalsent)
        while True:
            status, writing, written = agent.storage_status()
            if callback is not None:
                callback(imgname, totalread, inputsize, written, outputsize)
            if writing is False:
                break
            time.sleep(0.5)
        self._socket.close()
        self._socket = None
        if outputsize and written != outputsize:
            raise IOError(f'image write failed: wrote {written} out of {outputsize} bytes')

    def path(self):
        return self._path

    def prepare(self, socket, output_size=None, compression=None):
        compr = None
        if compression is None:
            compr = Compression.from_extension(self._path)
        self._inputsize = self.size
        self._outputsize = output_size
        self._socket = socket
        # if image is uncompressed, we compress on the fly
        if compr == CONSTS.IMAGE.RAW.value:
            compr = CONSTS.IMAGE.ZST.value
        self._agent.storage_compression(compr)
        self._lastreport = time.time()
        self._totalread = 0

    def progress(self):
        # Report progress via callback
        callback = self._callback
        imgname = self._imgname
        inputsize = self._inputsize
        totalread = self._totalread
        outputsize = self._outputsize
        if callback is not None and time.time() - self._lastreport >= 1:
            _, _, written = self._agent.storage_status()
            callback(imgname, totalread, inputsize, written, outputsize)
            self._lastreport = time.time()

    @property
    def size(self):
        return 0

    def _write_to_storage(self, data):
        self._socket.send(data)
        self._totalsent += len(data)


class ImageLocal(ImageFile):
    """ An image from the local file-system to be copied over to the shared
        storage. """

    def __init__(self, path, agent, session, blksz, callback=None):
        super().__init__(path, agent, session, blksz, callback)

    def bmap(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read()
        return None

    def copy(self):
        if os.path.exists(self._path) is False:
            raise IOError(f'{self._path}: image not found!')

        image = open(self._path, 'rb')
        comp_on_the_fly = False
        if Compression.from_extension(self._path) == CONSTS.IMAGE.RAW.value:
            cctx = zstd.ZstdCompressor(level=1)
            comp_on_the_fly = True
            inputstream = cctx.stream_reader(image)
        else:
            inputstream = image

        try:
            while (data := inputstream.read(self._blksz)):
                self._totalread = image.tell()
                self.progress()
                self._write_to_storage(data)

        finally:
            if comp_on_the_fly:
                inputstream.close()
            else:
                image.close()

    @property
    def size(self):
        st = os.stat(self._path)
        return st.st_size


class ImageS3(ImageFile):
    """ An image to be downloaded from a S3 bucket """

    def __init__(self, path, agent, session, blksz, callback=None):
        super().__init__(path, agent, session, blksz, callback)
        self._object = None

        from urllib.parse import urlparse
        url = urlparse(self._path)
        self._bucket = url.hostname
        self._key = url.path[1:]

    def bmap(self, path):
        from urllib.parse import urlparse

        url = urlparse(path)
        bucket = url.hostname
        key = url.path[1:]
        result = None

        if bucket != self._bucket:
            raise RuntimeError('bmap shall be downloaded from the same S3 '
                               'bucket as the image!')

        bmap = self._open(key)
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
            from boto3.s3.transfer import TransferConfig

            config = TransferConfig(use_threads=False)
            bmap.download_file(Filename=tmp.name, Config=config)
            bmap = None

            tmp.close()
            with open(tmp.name, 'r') as f:
                result = f.read()
            os.unlink(tmp.name)

        return result

    def copy(self):
        if self._object is None:
            self._object = self._open()

        from boto3.s3.transfer import TransferConfig
        config = TransferConfig(use_threads=False)
        self._object.download_fileobj(self, Config=config)

    @property
    def size(self):
        if self._object is None:
            self._object = self._open()

        result = None
        if self._object is not None:
            result = self._object.content_length
        return result

    def write(self, data):
        """ called by boto3 as data gets downloaded from S3 """

        dataread = len(data)
        self._totalread += dataread

        # Write block to shared storage device
        self.progress()
        self._write_to_storage(data)

        return dataread

    def _open(self, key=None):
        if key is None:
            key = self._key

        import boto3
        s3 = boto3.resource('s3')
        return s3.Object(self._bucket, key)
