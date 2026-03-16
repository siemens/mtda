# ---------------------------------------------------------------------------
# Remote console support for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2026 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# Local imports
from mtda.console.output import ConsoleOutput
import mtda.constants as CONSTS

# System imports
import grpc

from mtda.grpc import mtda_pb2, mtda_pb2_grpc


class RemoteConsole(ConsoleOutput):
    """Streams console output and events from a remote MTDA agent via the
    gRPC Subscribe server-streaming RPC.  Replaces the previous ZMQ SUB
    socket implementation."""

    # Topics this console cares about (bytes form for comparison)
    TOPICS = {CONSTS.CHANNEL.CONSOLE, CONSTS.CHANNEL.EVENTS}

    def __init__(self, host, port, screen):
        ConsoleOutput.__init__(self, screen)
        self.host = host
        self.port = port
        self._channel = None
        self._stream = None

    def _topics(self):
        """Return the set of byte-string topics accepted by this console."""
        return self.TOPICS

    def dispatch(self, topic, data):
        """Route an incoming message to the right handler.
        topic is always bytes (b'CON', b'EVT', or b'MON')."""
        if topic == CONSTS.CHANNEL.EVENTS:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            self.on_event(data)
        else:
            if isinstance(data, str):
                data = data.encode("utf-8")
            self.write(data)

    def reader(self):
        target = f"{self.host}:{self.port}"
        self._channel = grpc.insecure_channel(target)
        stub = mtda_pb2_grpc.MtdaServiceStub(self._channel)
        try:
            self._stream = stub.Subscribe(mtda_pb2.Empty())
            topics = self._topics()
            for msg in self._stream:
                if self.exiting:
                    break
                # Normalise topic to bytes for consistent comparison
                topic = msg.topic
                if isinstance(topic, str):
                    topic = topic.encode("utf-8")
                if topic in topics:
                    self.dispatch(topic, msg.data)
        except grpc.RpcError:
            pass
        finally:
            self._stream = None

    def stop(self):
        super().stop()
        if self._stream is not None:
            try:
                self._stream.cancel()
            except Exception:
                pass
            self._stream = None
        if self._channel is not None:
            self._channel.close()
            self._channel = None


class RemoteMonitor(RemoteConsole):
    """Like RemoteConsole but subscribes to the MON (monitor) topic."""

    TOPICS = {CONSTS.CHANNEL.MONITOR, CONSTS.CHANNEL.EVENTS}
