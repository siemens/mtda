# ---------------------------------------------------------------------------
# Writer to shared storage devices
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import bz2
import threading
import mtda.constants as CONSTS
import zlib
import zstandard as zstd
import lzma
import zmq


class AsyncImageWriter:

    def __init__(self, mtda, storage, dataport, compression=CONSTS.IMAGE.RAW):
        self.mtda = mtda
        self.storage = storage
        self.compression = compression
        self._blksz = CONSTS.WRITER.WRITE_SIZE
        self._dataport = dataport
        self._exiting = False
        self._failed = False
        self._session = None
        self._size = 0
        self._socket = None
        self._thread = None
        self._receiving = False
        self._writing = False
        self._written = 0
        self._zdec = None

    @property
    def compression(self):
        self.mtda.debug(3, "storage.writer.compression.get()")

        result = self._compression

        self.mtda.debug(3, f"storage.writer.compression.get(): {str(result)}")
        return result

    @compression.setter
    def compression(self, compression):
        self.mtda.debug(3, "storage.writer.compression.set()")

        compression = CONSTS.IMAGE(compression)
        if compression == CONSTS.IMAGE.RAW:
            self._write = self.write_raw
        elif compression == CONSTS.IMAGE.BZ2:
            self._write = self.write_bz2
        elif compression == CONSTS.IMAGE.GZ:
            self._write = self.write_gz
        elif compression == CONSTS.IMAGE.ZST:
            self._write = self.write_zst
        elif compression == CONSTS.IMAGE.XZ:
            self._write = self.write_xz
        else:
            raise ValueError("unsupported image compression!")
        self._compression = compression

        result = compression
        self.mtda.debug(3, f"storage.writer.compression.set(): {str(result)}")

    @property
    def failed(self):
        return self._failed

    def flush(self, size):
        self.mtda.debug(3, "mtda.storage.writer.flush()")

        result = None
        self._receiving = False
        self._size = size

        self.mtda.debug(3, f"storage.writer.flush(): {result}")
        return result

    def start(self, session):
        self.mtda.debug(3, "mtda.storage.writer.start()")

        self._session = session
        context = zmq.Context()
        timeout = CONSTS.WRITER.RECV_TIMEOUT * 1000

        self._socket = context.socket(zmq.PULL)
        self._socket.bind(f"tcp://*:{self._dataport}")
        self._socket.setsockopt(zmq.RCVTIMEO, timeout)

        endpoint = self._socket.getsockopt_string(zmq.LAST_ENDPOINT)
        result = int(endpoint.split(":")[-1])

        self._thread = threading.Thread(target=self.worker,
                                        daemon=True, name='writer')
        self._thread.start()

        self.mtda.debug(3, f"storage.writer.start(): {result}")
        return result

    def stop(self):
        self.mtda.debug(3, "storage.writer.stop()")

        result = None
        self._exiting = True

        if self._thread is not None:
            self.mtda.debug(2, "storage.writer.stop(): waiting on thread...")
            self._thread.join()

        self.mtda.debug(2, "storage.writer.stop(): all done")

        self._thread = None
        self._zdec = None

        self.mtda.debug(3, f"storage.writer.stop(): {result}")
        return result

    def worker(self):
        self.mtda.debug(3, "storage.writer.worker()")

        mtda = self.mtda
        received = 0
        result = None
        self._exiting = False
        self._failed = False
        self._receiving = True
        self._written = 0
        self._writing = True
        while self._exiting is False:
            try:
                chunk = self._socket.recv()
                received += len(chunk)
                mtda.session_ping(self._session)
                self._write(chunk)
            except zmq.Again:
                if self._receiving is False:
                    if self._size > 0 and received == self._size:
                        mtda.debug(1, "storage.writer.worker(): transfer complete")
                        break
                self._failed = True
                mtda.debug(1, "storage.writer.worker(): timeout "
                              f"(recv'd {received} / {self._size})")
            except Exception as e:
                self._failed = True
                mtda.debug(1, f"storage.writer.worker(): {e}")
                break

        self._receiving = False
        self._writing = False
        if self._failed is True:
            mtda.debug(1, "storage.writer.worker(): "
                          "write or decompression error!")

        if self._socket:
            self._socket.close()
            self._socket = None

        mtda.debug(3, f"storage.writer.worker(): {result}")
        return result

    def write_raw(self, data):
        self.mtda.debug(3, "storage.writer.write_raw()")

        result = None
        try:
            result = self.storage.write(data)
        except OSError as e:
            self.mtda.debug(1, f"storage.writer.write_raw(): {e}")
            raise

        self.mtda.debug(3, f"storage.writer.write_raw(): {str(result)}")
        return result

    def write_gz(self, data):
        self.mtda.debug(3, "storage.writer.write_gz()")

        # Create a zlib decompressor when called for the first time
        if self._zdec is None:
            self._zdec = zlib.decompressobj(16+zlib.MAX_WBITS)

        try:
            cont = True
            result = None
            while cont is True:
                uncompressed = self._zdec.decompress(data, self._blksz)
                data = self._zdec.unconsumed_tail
                cont = len(data) > 0
                result = self.storage.write(uncompressed)
        except (OSError, zlib.error) as e:
            self.mtda.debug(1, f"storage.writer.write_gz(): {e}")
            raise

        self.mtda.debug(3, f"storage.writer.write_gz(): {str(result)}")
        return result

    def write_bz2(self, data):
        self.mtda.debug(3, "storage.writer.write_bz2()")

        # Create a bz2 decompressor when called for the first time
        if self._zdec is None:
            self._zdec = bz2.BZ2Decompressor()

        try:
            cont = True
            result = None
            while cont is True:
                uncompressed = self._zdec.decompress(data, self._blksz)
                result = self.storage.write(uncompressed)
                cont = self._zdec.needs_input is False
                data = b''
        except EOFError:
            result = 0
        except OSError as e:
            self.mtda.debug(1, f"storage.writer.write_bz2(): {e}")
            raise

        self.mtda.debug(3, f"storage.writer.write_bz2(): {str(result)}")
        return result

    def write_zst(self, data):
        self.mtda.debug(3, "storage.writer.write_zst()")

        result = None
        # Create a decompressor when called for the first time
        if self._zdec is None:
            dctx = zstd.ZstdDecompressor()
            self._zdec = dctx.stream_writer(self.storage)
        try:
            result = self._zdec.write(data)
        except OSError as e:
            self.mtda.debug(1, f"storage.writer.write_zst(): {e}")
            raise

        self.mtda.debug(3, f"storage.writer.write_zst(): {str(result)}")
        return result

    def write_xz(self, data):
        self.mtda.debug(3, "storage.writer.write_xz()")

        # Create a xz decompressor when called for the first time
        if self._zdec is None:
            self._zdec = lzma.LZMADecompressor()

        try:
            cont = True
            result = None
            while cont is True:
                uncompressed = self._zdec.decompress(data, self._blksz)
                result = self.storage.write(uncompressed)
                cont = self._zdec.needs_input is False
                data = b''
        except EOFError:
            result = 0
        except OSError as e:
            self.mtda.debug(1, f"storage.writer.write_xz(): {e}")
            raise

        self.mtda.debug(3, f"storage.writer.write_xz(): {str(result)}")
        return result

    @property
    def writing(self):
        return self._writing

    @property
    def written(self):
        written = self.storage.tell()
        if written is not None:
            self._written = written
        return self._written
