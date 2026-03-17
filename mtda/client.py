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


import codecs
import json
import os
import queue
import random
import socket
import subprocess
import tempfile
import threading
import time
import zstandard as zstd

import grpc

from mtda.main import MultiTenantDeviceAccess
from mtda.grpc import mtda_pb2, mtda_pb2_grpc
from mtda.utils import Compression, BmapUtils
import mtda.constants as CONSTS


class _GrpcImpl:
    """Thin wrapper around the generated gRPC stub that presents the same
    call interface as MultiTenantDeviceAccess (plain Python return values)
    so that the rest of client.py needs no changes."""

    def __init__(self, stub, session, timeout):
        self._stub = stub
        self._session = session
        self._timeout = timeout

    def _meta(self):
        return (('mtda-session', self._session),) if self._session else ()

    def _call(self, method, request):
        return method(request, metadata=self._meta(),
                      timeout=self._timeout)

    # --- Agent ---

    def agent_version(self, **kwargs):
        return self._call(self._stub.AgentVersion,
                          mtda_pb2.Empty()).version or None

    # --- Power / command ---

    def command(self, args, **kwargs):
        return self._call(self._stub.Command,
                          mtda_pb2.CommandRequest(args=args)).value

    # --- Config ---

    def config_set_power_timeout(self, timeout, **kwargs):
        return self._call(self._stub.ConfigSetPowerTimeout,
                          mtda_pb2.SetPowerTimeoutRequest(
                              timeout=timeout)).value

    def config_set_session_timeout(self, timeout, **kwargs):
        return self._call(self._stub.ConfigSetSessionTimeout,
                          mtda_pb2.SetSessionTimeoutRequest(
                              timeout=timeout)).value

    # --- Console ---

    def console_clear(self, **kwargs):
        r = self._call(self._stub.ConsoleClear, mtda_pb2.Empty())
        return r.value if r.has_value else None

    def console_dump(self, **kwargs):
        r = self._call(self._stub.ConsoleDump, mtda_pb2.Empty())
        return r.value if r.has_value else None

    def console_flush(self, **kwargs):
        r = self._call(self._stub.ConsoleFlush, mtda_pb2.Empty())
        return r.value if r.has_value else None

    def console_head(self, **kwargs):
        r = self._call(self._stub.ConsoleHead, mtda_pb2.Empty())
        return r.value if r.has_value else None

    def console_lines(self, **kwargs):
        return self._call(self._stub.ConsoleLines, mtda_pb2.Empty()).lines

    def console_print(self, data, **kwargs):
        r = self._call(self._stub.ConsolePrint,
                       mtda_pb2.ConsolePrintRequest(data=data))
        return r.value if r.has_value else None

    def console_prompt(self, newPrompt=None, **kwargs):
        req = mtda_pb2.ConsolePromptRequest(
            new_prompt=newPrompt or '',
            get_only=(newPrompt is None))
        r = self._call(self._stub.ConsolePrompt, req)
        return r.value if r.has_value else None

    def console_run(self, cmd, **kwargs):
        r = self._call(self._stub.ConsoleRun,
                       mtda_pb2.ConsoleRunRequest(cmd=cmd))
        return r.value if r.has_value else None

    def console_send(self, data, raw=False, **kwargs):
        if not isinstance(data, bytes):
            if raw is False:
                data = codecs.escape_decode(bytes(data, "utf-8"))[0]
            else:
                data = data.encode("utf-8")
        r = self._call(self._stub.ConsoleSend,
                       mtda_pb2.ConsoleSendRequest(data=data, raw=raw))
        return r.value if r.has_value else None

    def console_tail(self, **kwargs):
        r = self._call(self._stub.ConsoleTail, mtda_pb2.Empty())
        return r.value if r.has_value else None

    def console_toggle(self, **kwargs):
        self._call(self._stub.ConsoleToggle, mtda_pb2.Empty())

    def console_wait(self, what, timeout=None, **kwargs):
        req = mtda_pb2.ConsoleWaitRequest(
            what=what, timeout=float(timeout or 0))
        lines = [r.line for r in self._stub.ConsoleWait(
            req, metadata=self._meta(), timeout=self._timeout)]
        return '\n'.join(lines) if lines else None

    # --- Env ---

    def env_get(self, name, default=None, **kwargs):
        r = self._call(self._stub.EnvGet,
                       mtda_pb2.EnvGetRequest(name=name,
                                              default=default or ''))
        return r.value if r.has_value else None

    def env_set(self, name, value, **kwargs):
        r = self._call(self._stub.EnvSet,
                       mtda_pb2.EnvSetRequest(name=name, value=value))
        return r.value if r.has_value else None

    # --- Keyboard ---

    def keyboard_press(self, key, repeat=1, ctrl=False, shift=False,
                       alt=False, meta=False, **kwargs):
        r = self._call(self._stub.KeyboardPress,
                       mtda_pb2.KeyboardPressRequest(
                           key=key, repeat=repeat,
                           ctrl=ctrl, shift=shift, alt=alt, meta=meta))
        return r.value if r.has_value else None

    def keyboard_write(self, what, **kwargs):
        r = self._call(self._stub.KeyboardWrite,
                       mtda_pb2.KeyboardWriteRequest(what=what))
        return r.value if r.has_value else None

    # --- Mouse ---

    def mouse_move(self, x, y, buttons, **kwargs):
        r = self._call(self._stub.MouseMove,
                       mtda_pb2.MouseMoveRequest(x=x, y=y, buttons=buttons))
        return r.value if r.has_value else None

    # --- Monitor ---

    def monitor_send(self, data, raw=False, **kwargs):
        if not isinstance(data, bytes):
            if raw is False:
                data = codecs.escape_decode(bytes(data, "utf-8"))[0]
            else:
                data = data.encode("utf-8")
        r = self._call(self._stub.MonitorSend,
                       mtda_pb2.MonitorSendRequest(data=data, raw=raw))
        return r.value if r.has_value else None

    def monitor_wait(self, what, timeout=None, **kwargs):
        req = mtda_pb2.MonitorWaitRequest(
            what=what, timeout=float(timeout or 0))
        lines = [r.line for r in self._stub.MonitorWait(
            req, metadata=self._meta(), timeout=self._timeout)]
        return '\n'.join(lines) if lines else None

    # --- Storage ---

    def storage_bmap_dict(self, bmapDict, **kwargs):
        if bmapDict is None:
            req = mtda_pb2.StorageBmapDictRequest(has_dict=False, json='')
        else:
            req = mtda_pb2.StorageBmapDictRequest(
                has_dict=True, json=json.dumps(bmapDict))
        return self._call(self._stub.StorageBmapDict, req).value

    def storage_close(self, **kwargs):
        return self._call(self._stub.StorageClose, mtda_pb2.Empty()).value

    def storage_commit(self, **kwargs):
        return self._call(self._stub.StorageCommit, mtda_pb2.Empty()).value

    def storage_compression(self, compression, **kwargs):
        r = self._call(self._stub.StorageCompression,
                       mtda_pb2.StorageCompressionRequest(
                           compression=str(int(compression)) if compression is not None else ''))
        return r.value if r.has_value else None

    def storage_flush(self, size, **kwargs):
        return self._call(self._stub.StorageFlush,
                          mtda_pb2.StorageFlushRequest(size=size)).value

    def storage_mount(self, part=None, **kwargs):
        req = mtda_pb2.StorageMountRequest(
            part=part or '', has_part=(part is not None))
        return self._call(self._stub.StorageMount, req).value

    def storage_network(self, **kwargs):
        return self._call(self._stub.StorageNetwork, mtda_pb2.Empty()).value

    def storage_open(self, size=0, **kwargs):
        self._call(self._stub.StorageOpen,
                   mtda_pb2.StorageOpenRequest(size=size))
        return None

    def storage_rollback(self, **kwargs):
        return self._call(self._stub.StorageRollback, mtda_pb2.Empty()).value

    def storage_status(self, **kwargs):
        r = self._call(self._stub.StorageStatus, mtda_pb2.Empty())
        return r.status, r.writing, r.written

    def storage_swap(self, **kwargs):
        return self._call(self._stub.StorageSwap, mtda_pb2.Empty()).status

    def storage_to_host(self, **kwargs):
        return self._call(self._stub.StorageToHost, mtda_pb2.Empty()).value

    def storage_to_target(self, **kwargs):
        return self._call(self._stub.StorageToTarget, mtda_pb2.Empty()).value

    def storage_toggle(self, **kwargs):
        return self._call(self._stub.StorageToggle, mtda_pb2.Empty()).status

    def storage_update(self, dst, size, **kwargs):
        self._call(self._stub.StorageUpdate,
                   mtda_pb2.StorageUpdateRequest(dst=dst, size=size))
        return None

    # --- Target ---

    def target_lock(self, **kwargs):
        return self._call(self._stub.TargetLock, mtda_pb2.Empty()).value

    def target_locked(self, **kwargs):
        return self._call(self._stub.TargetLocked, mtda_pb2.Empty()).value

    def target_off(self, **kwargs):
        return self._call(self._stub.TargetOff, mtda_pb2.Empty()).value

    def target_on(self, **kwargs):
        return self._call(self._stub.TargetOn, mtda_pb2.Empty()).value

    def target_status(self, **kwargs):
        return self._call(self._stub.TargetStatus, mtda_pb2.Empty()).status

    def target_toggle(self, **kwargs):
        return self._call(self._stub.TargetToggle, mtda_pb2.Empty()).status

    def target_unlock(self, **kwargs):
        return self._call(self._stub.TargetUnlock, mtda_pb2.Empty()).value

    def target_uptime(self, **kwargs):
        return self._call(self._stub.TargetUptime, mtda_pb2.Empty()).uptime

    def toggle_timestamps(self, **kwargs):
        return self._call(
            self._stub.ToggleTimestamps, mtda_pb2.Empty()).value

    # --- USB ---

    def usb_find_by_class(self, className, **kwargs):
        r = self._call(self._stub.UsbFindByClass,
                       mtda_pb2.UsbClassRequest(class_name=className))
        return r.value if r.has_value else None

    def usb_has_class(self, className, **kwargs):
        return self._call(self._stub.UsbHasClass,
                          mtda_pb2.UsbClassRequest(
                              class_name=className)).value

    def usb_off(self, ndx, **kwargs):
        self._call(self._stub.UsbOff, mtda_pb2.UsbIndexRequest(ndx=ndx))

    def usb_off_by_class(self, className, **kwargs):
        return self._call(self._stub.UsbOffByClass,
                          mtda_pb2.UsbClassRequest(
                              class_name=className)).value

    def usb_on(self, ndx, **kwargs):
        self._call(self._stub.UsbOn, mtda_pb2.UsbIndexRequest(ndx=ndx))

    def usb_on_by_class(self, className, **kwargs):
        return self._call(self._stub.UsbOnByClass,
                          mtda_pb2.UsbClassRequest(
                              class_name=className)).value

    def usb_ports(self, **kwargs):
        return self._call(self._stub.UsbPorts, mtda_pb2.Empty()).ports

    def usb_status(self, ndx, **kwargs):
        return self._call(self._stub.UsbStatus,
                          mtda_pb2.UsbIndexRequest(ndx=ndx)).status

    def usb_toggle(self, ndx, **kwargs):
        self._call(self._stub.UsbToggle, mtda_pb2.UsbIndexRequest(ndx=ndx))

    # --- Video ---

    def video_format(self, **kwargs):
        r = self._call(self._stub.VideoFormat, mtda_pb2.Empty())
        return r.value if r.has_value else None

    def video_url(self, host='', opts=None, **kwargs):
        req = mtda_pb2.VideoUrlRequest(
            host=host or '',
            opts=opts or '',
            has_opts=(opts is not None))
        r = self._call(self._stub.VideoUrl, req)
        return r.value if r.has_value else None

    def close(self):
        if hasattr(self, '_channel'):
            self._channel.close()


class _LocalStorageSocket:
    """Socket-like adapter for local (in-process) storage writes.

    Calls impl.storage_write(data) which enqueues the chunk into the
    QueueDataStream that was set up by storage_open().  An empty bytes
    sentinel (b'') signals end-of-transfer to the background writer."""

    def __init__(self, impl, session):
        self._impl = impl
        self._session = session

    def send(self, data, flags=0):
        self._impl.storage_write(data, session=self._session)

    def close(self):
        pass  # nothing to tear down


class _GrpcStorageSocket:
    """Socket-like adapter that streams image chunks to the server via the
    gRPC StorageWrite client-streaming RPC.

    A background thread drives the streaming call; chunks are fed to it via
    an internal queue.  send() enqueues a chunk (blocking on back-pressure);
    an empty bytes sentinel (b'') signals end-of-transfer and causes the
    stream to be closed when close() is called."""

    def __init__(self, stub, session, timeout):
        self._stub = stub
        self._session = session
        self._timeout = timeout
        hwm = int(CONSTS.WRITER.HIGH_WATER_MARK / CONSTS.WRITER.READ_SIZE)
        self._queue = queue.Queue(maxsize=hwm)
        self._result = None
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name='grpc-storage-write')
        self._thread.start()

    def _chunk_iter(self):
        while True:
            chunk = self._queue.get()
            yield mtda_pb2.StorageChunkRequest(data=chunk)
            if not chunk:
                break

    def _run(self):
        meta = (('mtda-session', self._session),) if self._session else ()
        try:
            resp = self._stub.StorageWrite(
                self._chunk_iter(),
                metadata=meta,
                timeout=None,  # no timeout for streaming bulk transfer
            )
            self._result = resp.ok
        except Exception:
            self._result = False

    def send(self, data, flags=0):
        """Enqueue a chunk.  Blocks if the queue is full (back-pressure)."""
        self._queue.put(data)

    def close(self):
        """Wait for the streaming RPC to finish."""
        self._thread.join()


class Client:

    @staticmethod
    def _generate_session():
        """Return a session name from the system word list, $MTDA_SESSION, or a
        host/user fallback.  Only ASCII words are considered so the result is
        always safe to use as a gRPC metadata value."""
        HOST = socket.gethostname()
        USER = os.getenv("USER")
        WORDS = "/usr/share/dict/words"
        if os.path.exists(WORDS):
            words = [w for w in open(WORDS).read().splitlines() if w.isascii()]
            name = random.choice(words)
            if name.endswith("'s"):
                name = name.replace("'s", "")
        elif USER is not None and HOST is not None:
            name = f"{USER}@{HOST}"
        else:
            name = "mtda"
        return os.getenv('MTDA_SESSION', name)

    def __init__(self, host=None, session=None, config_files=None,
                 timeout=CONSTS.RPC.TIMEOUT):
        """
        Client to control mtda device
        :param host:    hostname or ip of mtda device
        :param session: mtda session id
        :param config_files: configuration filenames
        :param timeout: RPC timeout in seconds
        """
        if session is None:
            session = Client._generate_session()

        agent = MultiTenantDeviceAccess()
        agent.load_config(host, config_files=config_files)
        if agent.remote is not None:
            target = f'{agent.remote}:{agent.ctrlport}'
            channel = grpc.insecure_channel(target)
            stub = mtda_pb2_grpc.MtdaServiceStub(channel)
            impl = _GrpcImpl(stub, session, timeout)
            impl._channel = channel
            self._impl = impl
        else:
            self._impl = agent

        self._agent = agent
        self._session = session
        self._data = None

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
        self._impl.storage_open(size, session=session)
        self._data = self._storage_socket()
        return self._data

    def _storage_socket(self):
        if isinstance(self._impl, _GrpcImpl):
            return _GrpcStorageSocket(
                self._impl._stub,
                self._impl._session,
                self._impl._timeout,
            )
        else:
            return _LocalStorageSocket(self._impl, self._session)

    def storage_update(self, dest, src=None, **kwargs):
        session = kwargs.get('session', self._session)

        path = dest if src is None else src
        st = os.stat(path)
        size = st.st_size

        self._impl.storage_update(dest, size, session=session)
        self._data = self._storage_socket()

        blksz = self._agent.blksz
        impl = self._impl

        # Get file handler from specified path
        file = ImageFile.new(path, impl, session, blksz)

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

    def storage_write_image(self, path):
        blksz = self._agent.blksz
        impl = self._impl
        session = self._session

        # Get file handler from specified path
        file = ImageFile.new(path, impl, session, blksz)

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
                    bmapDict = BmapUtils.parseBmap(bmap, bmap_path)
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

    def start(self):
        return self._agent.start()

    def stop(self):
        if self._agent.remote is not None:
            self._impl.close()
        else:
            self._agent.stop()

    def remote(self):
        return self._agent.remote

    def ctrlport(self):
        return self._agent.ctrlport

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

    def new(path, agent, session, blksz):
        if path.startswith('s3:'):
            return ImageS3(path, agent, session, blksz)
        else:
            return ImageLocal(path, agent, session, blksz)

    def __init__(self, path, agent, session, blksz):
        self._agent = agent
        self._blksz = blksz
        self._imgname = os.path.basename(path)
        self._inputsize = 0
        self._path = path
        self._session = session
        self._totalread = 0
        self._totalsent = 0

    def bmap(self, path):
        return None

    def flush(self):
        # Signal end-of-transfer, then wait for background writes to complete
        agent = self._agent
        self._socket.send(b'')
        self._socket.close()
        self._socket = None
        writing = True
        while writing:
            _, writing, written = agent.storage_status()
            time.sleep(0.5)
        success = agent.storage_flush(self._totalsent)
        if not success:
            raise IOError('image write failed!')

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

    @property
    def size(self):
        return 0

    def _write_to_storage(self, data):
        self._socket.send(data)
        self._totalsent += len(data)


class ImageLocal(ImageFile):
    """ An image from the local file-system to be copied over to the shared
        storage. """

    def __init__(self, path, agent, session, blksz):
        super().__init__(path, agent, session, blksz)

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

    def __init__(self, path, agent, session, blksz):
        super().__init__(path, agent, session, blksz)
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
        self._write_to_storage(data)

        return dataread

    def _open(self, key=None):
        if key is None:
            key = self._key

        import boto3
        s3 = boto3.resource('s3')
        return s3.Object(self._bucket, key)
