# ---------------------------------------------------------------------------
# Writer to shared storage devices
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import bz2
import queue
import threading
import mtda.constants as CONSTS
import zlib
import zstandard as zstd
import lzma


class AsyncImageWriter(queue.Queue):

    def __init__(self, mtda, storage, compression=CONSTS.IMAGE.RAW):
        self.mtda = mtda
        self.storage = storage
        self.compression = compression
        self._blksz = CONSTS.WRITER.WRITE_SIZE
        self._exiting = False
        self._failed = False
        self._thread = None
        self._writing = False
        self._written = 0
        self._zdec = None
        super().__init__(maxsize=CONSTS.WRITER.QUEUE_SLOTS)

    @property
    def compression(self):
        self.mtda.debug(3, "storage.writer.compression.get()")

        result = self._compression

        self.mtda.debug(3, "storage.writer.compression.get(): "
                           "%s" % str(result))
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
        self.mtda.debug(3, "storage.writer.compression.set(): "
                           "%s" % str(result))

    @property
    def failed(self):
        return self._failed

    def put(self, chunk, block=True, timeout=None):
        self.mtda.debug(3, "storage.writer.put()")

        if self.storage is None:
            self.mtda.debug(1, "storage.writer.put(): no storage!")
            raise IOError("no storage!")
        result = super().put(chunk, block, timeout)

        self.mtda.debug(3, "storage.writer.put(): %s" % str(result))
        return result

    def start(self):
        self.mtda.debug(3, "mtda.storage.writer.start()")

        result = None
        self._thread = threading.Thread(target=self.worker,
                                        daemon=True, name='writer')
        self._thread.start()

        self.mtda.debug(3, "storage.writer.start(): %s" % str(result))
        return result

    def stop(self):
        self.mtda.debug(3, "storage.writer.stop()")

        result = None
        self.mtda.debug(2, "storage.writer.stop(): waiting on queue...")
        self.join()

        if self._thread is not None:
            self.mtda.debug(2, "storage.writer.stop(): waiting on thread...")
            self._exiting = True
            self.put(b'')
            self._thread.join()

        self.mtda.debug(2, "storage.writer.stop(): all done")
        self._thread = None
        self._zdec = None

        self.mtda.debug(3, "storage.writer.stop(): %s" % str(result))
        return result

    def worker(self):
        self.mtda.debug(3, "storage.writer.worker()")

        result = None
        self._exiting = False
        self._failed = False
        self._written = 0
        while self._exiting is False:
            chunk = self.get()
            if self._exiting is False:
                self._writing = True
                self._write(chunk)
                self._writing = False
            self.task_done()
            if self._failed is True:
                self.mtda.debug(1, "storage.writer.worker(): "
                                   "write or decompression error!")
                break

        self.mtda.debug(3, "storage.writer.worker(): %s" % str(result))
        return result

    def write_raw(self, data, session=None):
        self.mtda.debug(3, "storage.writer.write_raw()")

        result = None
        try:
            result = self.storage.write(data)
            self._written += result if result is not None else 0
        except OSError as e:
            self.mtda.debug(1, "storage.writer.write_raw(): "
                               "%s" % str(e.args[0]))
            self._failed = True

        self.mtda.debug(3, "storage.writer.write_raw(): %s" % str(result))
        return result

    def write_gz(self, data, session=None):
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
                self._written += result if result is not None else 0
        except (OSError, zlib.error) as e:
            self.mtda.debug(1, "storage.writer.write_gz(): "
                               "%s" % str(e.args[0]))
            self._failed = True

        self.mtda.debug(3, "storage.writer.write_gz(): %s" % str(result))
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
                self._written += result if result is not None else 0
                cont = self._zdec.needs_input is False
                data = b''
        except EOFError:
            result = 0
        except OSError as e:
            self.mtda.debug(1, "storage.writer.write_bz2(): "
                               "%s" % str(e.args[0]))
            self._failed = True

        self.mtda.debug(3, "storage.writer.write_bz2(): %s" % str(result))
        return result

    def write_zst(self, data):
        self.mtda.debug(3, "storage.writer.write_zst()")

        # Create a decompressor when called for the first time
        if self._zdec is None:
            dctx = zstd.ZstdDecompressor()
            self._zdec = dctx.stream_writer(self.storage)
        try:
            result = self._zdec.write(data)
            self._written += result if result is not None else 0
        except OSError:
            self.mtda.debug(1, "storage.writer.write_zst(): write error!")
            self._failed = True

        self.mtda.debug(3, "storage.writer.write_zst(): %s" % str(result))
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
                self._written += result if result is not None else 0
                cont = self._zdec.needs_input is False
                data = b''
        except EOFError:
            result = 0
        except OSError as e:
            self.mtda.debug(1, "storage.writer.write_xz(): "
                               "%s" % str(e.args[0]))
            self._failed = True

        self.mtda.debug(3, "storage.writer.write_xz(): %s" % str(result))
        return result

    @property
    def writing(self):
        return self._writing

    @property
    def written(self):
        return self._written
