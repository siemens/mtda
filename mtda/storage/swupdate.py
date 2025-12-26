# ---------------------------------------------------------------------------
# swupdate storage driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import mtda.constants as CONSTS
from mtda.storage.controller import StorageController
import mtda.storage.helpers.swupdate_ipc as IPC
import socket
import ctypes


class SWUpdate(StorageController):
    def __init__(self, mtda):
        self.mtda = mtda
        self.writtenBytes = 0
        self._ipc_socket = None

    def open(self):
        """ Open the shared storage device for I/O operations"""
        self.mtda.debug(2, "swupdate open")
        self.writtenBytes = 0

        self._ipc_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # TODO: should come from a constant
        self._ipc_socket.connect("/var/run/swupdate/sockinstctrl")
        self._perform_handshake()
        return True

    def close(self):
        self._ipc_socket.close()
        return True

    def status(self):
        return CONSTS.STORAGE.ON_HOST

    def tell(self):
        return self.writtenBytes

    def write(self, data):
        self._ipc_socket.sendall(data)
        self.writtenBytes += len(data)
        self.mtda.notify_write()
        return len(data)

    def _perform_handshake(self):
        sock = self._ipc_socket
        sock.sendall(self._create_ipc_header_msg())
        response = sock.recv(ctypes.sizeof(IPC.ipc_message))
        ack = IPC.ipc_message.from_buffer_copy(response)
        if ack.type.value != IPC.msgtype.ACK:
            raise Exception("SWupdate error")

    def _create_ipc_header_msg(self):
        # TODO: for testing we create a dryrun message
        req = IPC.swupdate_request(
            apiversion=IPC.SWUPDATE_API_VERSION,
            disable_store_swu=True,
            source=IPC.sourcetype.SOURCE_NETWORK,
            dry_run=IPC.run_type.RUN_DRYRUN)
        instmsg = IPC.instmsg(req=req)
        msgdata = IPC.msgdata(instmsg=instmsg)

        return IPC.ipc_message(
            magic=IPC.IPC_MAGIC,
            type=IPC.msgtype.REQ_INSTALL,
            data=msgdata)
