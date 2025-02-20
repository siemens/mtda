# ---------------------------------------------------------------------------
# Data streams for shared storage
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import abc
import zmq

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


class NetworkDataStream(DataStream):

    def __init__(self, dataport):
        self._dataport = dataport
        self._socket = None

    def prepare(self):

        context = zmq.Context()
        timeout = CONSTS.WRITER.RECV_TIMEOUT * 1000

        self._socket = context.socket(zmq.PULL)
        self._socket.setsockopt(zmq.RCVTIMEO, timeout)
        hwm = int(CONSTS.WRITER.HIGH_WATER_MARK / CONSTS.WRITER.WRITE_SIZE)
        self._socket.setsockopt(zmq.RCVHWM, hwm)

        self._socket.bind(f"tcp://*:{self._dataport}")
        endpoint = self._socket.getsockopt_string(zmq.LAST_ENDPOINT)
        result = int(endpoint.split(":")[-1])

        return result

    def close(self):
        self._socket.close()
        self._socket = None

    def push(self, data, callback=None):
        raise RuntimeError('data to be sent to the backend using zmq')

    def pop(self):
        try:
            chunk = self._socket.recv()
            return chunk
        except zmq.Again:
            raise RetryException()


class LocalDataStream(DataStream):

    def __init__(self):
        from queue import Queue

        self._maxsize = int(CONSTS.WRITER.HIGH_WATER_MARK / CONSTS.WRITER.WRITE_SIZE)
        self._low = int(self._maxsize * 0.25)
        self._high = int(self._maxsize * 0.75)
        self._prev = 0
        self._queue = Queue(maxsize=self._maxsize)

    def prepare(self):
        pass

    def close(self):
        self._queue = None

    def pop(self):
        return self._queue.get()

    def push(self, data, callback=None):
        self._queue.put(data)
        qsize = self._queue.qsize()
        prev = self._prev
        self._prev = qsize

        if qsize <= self._low:
            if prev > self._low:
                if callable(callback):
                    callback(CONSTS.STORAGE.QUEUE_LOW)

        elif qsize >= self._high:
            if prev < self._high:
                if callable(callback):
                    callback(CONSTS.STORAGE.QUEUE_HIGH)
