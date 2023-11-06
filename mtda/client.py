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
import tempfile
import time
import zerorpc

from mtda.main import MultiTenantDeviceAccess
import mtda.constants as CONSTS


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
            uri = "tcp://%s:%d" % (agent.remote, agent.ctrlport)
            self._impl = zerorpc.Client(
                heartbeat=min(timeout, CONSTS.RPC.HEARTBEAT),
                timeout=timeout)
            self._impl.connect(uri)
        else:
            self._impl = agent
        self._agent = agent

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
                name = "%s@%s" % (USER, HOST)
            else:
                name = "mtda"
            self._session = os.getenv('MTDA_SESSION', name)
        else:
            self._session = session

    def agent_version(self):
        return self._impl.agent_version()

    def config_set_power_timeout(self, timeout):
        return self._impl.config_set_power_timeout(timeout, self._session)

    def config_set_session_timeout(self, timeout):
        return self._impl.config_set_session_timeout(timeout, self._session)

    def console_prefix_key(self):
        return self._agent.console_prefix_key()

    def command(self, args):
        return self._impl.command(args, self._session)

    def console_clear(self):
        return self._impl.console_clear(self._session)

    def console_dump(self):
        return self._impl.console_dump(self._session)

    def console_flush(self):
        return self._impl.console_flush(self._session)

    def console_getkey(self):
        return self._agent.console_getkey()

    def console_init(self):
        return self._agent.console_init()

    def console_head(self):
        return self._impl.console_head(self._session)

    def console_lines(self):
        return self._impl.console_lines(self._session)

    def console_locked(self):
        return self._impl.console_locked(self._session)

    def console_print(self, data):
        return self._impl.console_print(data, self._session)

    def console_prompt(self, newPrompt=None):
        return self._impl.console_prompt(newPrompt, self._session)

    def console_remote(self, host, screen):
        return self._agent.console_remote(host, screen)

    def console_run(self, cmd):
        return self._impl.console_run(cmd, self._session)

    def console_send(self, data, raw=False):
        return self._impl.console_send(data, raw, self._session)

    def console_toggle(self):
        return self._agent.console_toggle(self._session)

    def console_tail(self):
        return self._impl.console_tail(self._session)

    def console_wait(self, what, timeout=None):
        return self._impl.console_wait(what, timeout, self._session)

    def env_get(self, name):
        return self._impl.env_get(name, self._session)

    def env_set(self, name, value):
        return self._impl.env_set(name, value, self._session)

    def keyboard_write(self, data):
        return self._impl.keyboard_write(data, self._session)

    def monitor_remote(self, host, screen):
        return self._agent.monitor_remote(host, screen)

    def monitor_send(self, data, raw=False):
        return self._impl.monitor_send(data, raw, self._session)

    def monitor_wait(self, what, timeout=None):
        return self._impl.monitor_wait(what, timeout, self._session)

    def pastebin_api_key(self):
        return self._agent.pastebin_api_key()

    def pastebin_endpoint(self):
        return self._agent.pastebin_endpoint()

    def power_locked(self):
        return self._impl.power_locked(self._session)

    def storage_bytes_written(self):
        return self._impl.storage_bytes_written(self._session)

    def storage_close(self):
        return self._impl.storage_close(self._session)

    def storage_locked(self):
        return self._impl.storage_locked(self._session)

    def storage_mount(self, part=None):
        return self._impl.storage_mount(part, self._session)

    def storage_open(self):
        tries = 60
        while tries > 0:
            tries = tries - 1
            status = self._impl.storage_open(self._session)
            if status is True:
                return
            time.sleep(1)
        raise IOError('shared storage could not be opened')

    def storage_status(self):
        return self._impl.storage_status(self._session)

    def storage_update(self, dest, src=None, callback=None):
        path = dest if src is None else src
        imgname = os.path.basename(path)
        try:
            st = os.stat(path)
            imgsize = st.st_size
            image = open(path, "rb")
        except FileNotFoundError:
            return False

        status = self._impl.storage_update(dest, 0, self._session)
        if status is False:
            image.close()
            return False

        self._impl.storage_compression(CONSTS.IMAGE.RAW.value, self._session)
        return self._storage_write(image, imgname, imgsize, callback)

    def storage_write_image(self, path, callback=None):
        blksz = self._agent.blksz
        impl = self._impl
        session = self._session

        if path.startswith('s3:'):
            file = ImageS3(path, impl, session, blksz, callback)
        else:
            file = ImageLocal(path, impl, session, blksz, callback)

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
                    print("discovered bmap file '{}'".format(bmap_path))
                    bmapDict = self.parseBmap(bmap, bmap_path)
                    self._impl.storage_bmap_dict(bmapDict, self._session)
                    image_size = bmapDict['ImageSize']
                    break
            except Exception:
                pass
            image_path, ext = os.path.splitext(image_path)
            if ext == "":
                print("No bmap file found at location of image")
                break

        # Open the shared storage device
        status = self.storage_open()
        if status is False:
            return False

        try:
            # Prepare for download/copy
            file.prepare(image_size)

            # Copy image to shared storage
            file.copy()

            # Wait for background writes to complete
            file.flush()

        except Exception:
            status = False
        finally:
            # Storage may be closed now
            self.storage_close()

        return status

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
            print("Error parsing '%s', probably not a bmap 2.0 file"
                  % bmap_path)
            return None
        return bmapDict

    def storage_to_host(self):
        return self._impl.storage_to_host(self._session)

    def storage_to_target(self):
        return self._impl.storage_to_target(self._session)

    def storage_swap(self):
        return self._impl.storage_swap(self._session)

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
            status = self._impl.target_lock(self._session)
            if retries <= 0 or status is True:
                break
            retries = retries - 1
            time.sleep(60)
        return status

    def target_locked(self):
        return self._impl.target_locked(self._session)

    def target_off(self):
        return self._impl.target_off(self._session)

    def target_on(self):
        return self._impl.target_on(self._session)

    def target_status(self):
        return self._impl.target_status(self._session)

    def target_toggle(self):
        return self._impl.target_toggle(self._session)

    def target_unlock(self):
        return self._impl.target_unlock(self._session)

    def target_uptime(self):
        return self._impl.target_uptime(self._session)

    def toggle_timestamps(self):
        return self._impl.toggle_timestamps()

    def usb_find_by_class(self, className):
        return self._impl.usb_find_by_class(className, self._session)

    def usb_has_class(self, className):
        return self._impl.usb_has_class(className, self._session)

    def usb_off(self, ndx):
        return self._impl.usb_off(ndx, self._session)

    def usb_off_by_class(self, className):
        return self._impl.usb_off_by_class(className, self._session)

    def usb_on(self, ndx):
        return self._impl.usb_on(ndx, self._session)

    def usb_on_by_class(self, className):
        return self._impl.usb_on_by_class(className, self._session)

    def usb_ports(self):
        return self._impl.usb_ports(self._session)

    def usb_status(self, ndx):
        return self._impl.usb_status(ndx, self._session)

    def usb_toggle(self, ndx):
        return self._impl.usb_toggle(ndx, self._session)

    def version(self):
        return self._agent.version

    def video_url(self, host="", opts=None):
        if host == "":
            host = os.getenv("MTDA_REMOTE", "")
        return self._impl.video_url(host, opts)


class ImageFile:
    """ Base class for image files (local or remote) """

    def __init__(self, path, agent, session, blksz, callback=None):
        self._agent = agent
        self._blksz = blksz
        self._callback = callback
        self._imgname = os.path.basename(path)
        self._inputsize = 0
        self._path = path
        self._session = session
        self._totalread = 0

    def bmap(self, path):
        return None

    def compression(self):
        path = self._path
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

    def flush(self):
        # Wait for background writes to complete
        agent = self._agent
        callback = self._callback
        imgname = self._imgname
        inputsize = self._inputsize
        totalread = self._totalread
        while True:
            status, writing, written = agent.storage_status(self._session)
            if callback is not None:
                callback(imgname, totalread, inputsize, written, None)
            if writing is False:
                break
            time.sleep(0.5)

    def path(self):
        return self._path

    def prepare(self, output_size=None):
        compr = self.compression()
        self._inputsize = self.size()
        self._outputsize = None
        if output_size is None:
            if compr == CONSTS.IMAGE.RAW.value:
                self._outputsize = self._inputsize
        self._agent.storage_compression(compr, self._session)
        self._lastreport = time.time()
        self._totalread = 0

    def progress(self):
        # Report progress via callback
        callback = self._callback
        imgname = self._imgname
        inputsize = self._inputsize
        totalread = self._totalread
        if callback is not None and time.time() - self._lastreport > 0.5:
            _, _, written = self._agent.storage_status(self._session)
            callback(imgname, totalread, inputsize, written, None)
            self._lastreport = time.time()

    def size(self):
        return None


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
            raise IOError('{}: image not found!'.format(self._path))

        image = open(self._path, 'rb')
        try:
            data = image.read(self._blksz)
            dataread = len(data)
            while self._totalread < self._inputsize:
                self._totalread += dataread
                self.progress()

                # Write block to shared storage device
                bytes_wanted = self._agent.storage_write(data, self._session)

                # Check what to do next
                if bytes_wanted < 0:
                    raise IOError('write or decompression error from the '
                                  'shared storage')
                elif bytes_wanted > 0:
                    # Read next block
                    data = image.read(bytes_wanted)
                    dataread = len(data)
                else:
                    # Agent may continue without further data
                    data = b''
                    dataread = 0

        finally:
            # Close the local image
            image.close()

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
        bytes_wanted = 0
        while bytes_wanted == 0:
            # Report progress
            self.progress()

            # Write downloaded data to storage
            bytes_wanted = self._agent.storage_write(data, self._session)
            if bytes_wanted == 0:
                # Agent may continue without further data
                data = b''
            elif bytes_wanted < 0:
                # Write failure
                raise IOError('write or decompression error')

        return dataread

    def _open(self, key=None):
        if key is None:
            key = self._key

        import boto3
        s3 = boto3.resource('s3')
        return s3.Object(self._bucket, key)
