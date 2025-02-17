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

from mtda.exceptions import RetryException


class AsyncImageWriter:

    def __init__(self, mtda, storage, compression=CONSTS.IMAGE.RAW):
        self.mtda = mtda
        self.storage = storage
        self.compression = compression
        self._blksz = CONSTS.WRITER.WRITE_SIZE
        self._exiting = False
        self._failed = False
        self._session = None
        self._size = 0
        self._socket = None
        self._stream = None
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

    def enqueue(self, data, callback=None):
        self.mtda.debug(3, "mtda.storage.writer.enqueue()")

        result = None
        if self._stream is not None:
            result = self._stream.push(data, callback)

        self.mtda.debug(3, f"storage.writer.enqueue(): {result}")
        return result

    @property
    def failed(self):
        return self._failed

    def flush(self, size):
        self.mtda.debug(3, "mtda.storage.writer.flush()")

        self._receiving = False
        self._size = size

        self.mtda.debug(2, "storage.writer.flush(): waiting on thread...")
        self._thread.join()
        result = not self._failed

        self.mtda.debug(3, f"storage.writer.flush(): {result}")
        return result

    def start(self, session, stream):
        self.mtda.debug(3, "mtda.storage.writer.start()")

        self._session = session
        self._stream = stream

        result = stream.prepare()
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
        tries = CONSTS.WRITER.RECV_RETRIES
        self._exiting = False
        self._failed = False
        self._receiving = True
        self._written = 0
        self._writing = True
        while self._exiting is False:
            try:
                chunk = self._stream.pop()
                if len(chunk) == 0:
                    mtda.debug(2, "storage.writer.worker(): empty chunk "
                                  "transfer complete")
                    break
                received += len(chunk)
                tries = CONSTS.WRITER.RECV_RETRIES
                mtda.session_ping(self._session)
                self._write(chunk)

            except RetryException:
                tries = tries - 1
                if self._receiving is False:
                    if self._size > 0 and received == self._size:
                        mtda.debug(2, "storage.writer.worker(): "
                                      "transfer complete")
                        break
                    mtda.debug(1, "storage.writer.worker(): "
                                  "incomplete transfer")
                    tries = 0

                retries = ""
                if tries > 0:
                    retries = f" {tries} retries left "

                total = ""
                if self._size > 0:
                    total = f" / {self._size}"

                mtda.debug(1, f"storage.writer.worker(): timeout!{retries} "
                              f"(recv'd {received}{total})")

                if tries == 0:
                    self._failed = True
                    break

            except Exception as e:
                import traceback
                self._failed = True
                mtda.debug(1, f"storage.writer.worker(): {e}")
                mtda.debug(1, traceback.format_exc())
                break

        self._receiving = False
        self._writing = False

        if self._stream:
            self._stream.close()
            self._stream = None

        if self._failed is True:
            mtda.debug(1, "storage.writer.worker(): "
                          "write or decompression error!")

        mtda.debug(3, "storage.writer.worker(): exit")

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
