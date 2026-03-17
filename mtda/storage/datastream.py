# ---------------------------------------------------------------------------
# Data streams for shared storage
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2026 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import abc
import queue

import mtda.constants as CONSTS
from mtda.exceptions import RetryException


class DataStream(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def prepare(self):
        """ Prepare the data stream"""

    @abc.abstractmethod
    def close(self):
        """ Close the data stream"""

    @abc.abstractmethod
    def push(self, data, callback):
        """ Push data from the client to the backend"""

    @abc.abstractmethod
    def pop(self):
        """ Get queued data from the backend"""


class QueueDataStream(DataStream):
    """In-process queue-based data stream used by the gRPC StorageWrite RPC.

    The server-side servicer pushes chunks onto the queue via push(); the
    background writer thread consumes them via pop().  An empty bytes object
    (b'') signals end-of-transfer — the writer thread will stop cleanly when
    it dequeues that sentinel."""

    def __init__(self):
        self._queue = queue.Queue(
            maxsize=int(
                CONSTS.WRITER.HIGH_WATER_MARK / CONSTS.WRITER.WRITE_SIZE
            )
        )

    def prepare(self):
        """No network socket required; return None (no port)."""
        return None

    def close(self):
        """Nothing to clean up."""
        pass

    def push(self, data, callback=None):
        """Enqueue a chunk of data.  Blocks if the queue is full (back-pressure)."""
        self._queue.put(data)
        if callback is not None:
            callback()

    def pop(self):
        """Dequeue the next chunk.  Raises RetryException on timeout so the
        writer can apply its retry/give-up logic."""
        try:
            return self._queue.get(timeout=CONSTS.WRITER.RECV_TIMEOUT)
        except queue.Empty:
            raise RetryException()
