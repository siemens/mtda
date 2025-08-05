# ---------------------------------------------------------------------------
# Helper class for images
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------
#
# The type definitions need to match the upstream protocol definitions in
# https://github.com/sbabic/swupdate/blob/master/include/network_ipc.h

import ctypes

# Constants
IPC_MAGIC = 0x14052001
SWUPDATE_API_VERSION = 0x1


# Enums
class msgtype(ctypes.c_int):
    REQ_INSTALL = 0
    ACK = 1
    NACK = 2
    GET_STATUS = 3
    POST_UPDATE = 4
    SWUPDATE_SUBPROCESS = 5
    SET_AES_KEY = 6
    SET_UPDATE_STATE = 7
    GET_UPDATE_STATE = 8
    REQ_INSTALL_EXT = 9
    SET_VERSIONS_RANGE = 10
    NOTIFY_STREAM = 11
    GET_HW_REVISION = 12
    SET_SWUPDATE_VARS = 13
    GET_SWUPDATE_VARS = 14


class CMD_TYPE(ctypes.c_int):
    CMD_ACTIVATION = 0
    CMD_CONFIG = 1
    CMD_ENABLE = 2
    CMD_GET_STATUS = 3
    CMD_SET_DOWNLOAD_URL = 4


class run_type(ctypes.c_int):
    RUN_DEFAULT = 0
    RUN_DRYRUN = 1
    RUN_INSTALL = 2


# Structures
class sourcetype(ctypes.c_int):
    SOURCE_UNKNOWN = 0
    SOURCE_FILE = 1
    SOURCE_NETWORK = 2
    SOURCE_USB = 3


class swupdate_request(ctypes.Structure):
    _fields_ = [
        ("apiversion", ctypes.c_uint),
        ("source", sourcetype),
        ("dry_run", run_type),
        ("len", ctypes.c_size_t),
        ("info", ctypes.c_char * 512),
        ("software_set", ctypes.c_char * 256),
        ("running_mode", ctypes.c_char * 256),
        ("disable_store_swu", ctypes.c_bool)
    ]


class status(ctypes.Structure):
    _fields_ = [
        ("current", ctypes.c_int),
        ("last_result", ctypes.c_int),
        ("error", ctypes.c_int),
        ("desc", ctypes.c_char * 2048)
    ]


class notify(ctypes.Structure):
    _fields_ = [
        ("status", ctypes.c_int),
        ("error", ctypes.c_int),
        ("level", ctypes.c_int),
        ("msg", ctypes.c_char * 2048)
    ]


class instmsg(ctypes.Structure):
    _fields_ = [
        ("req", swupdate_request),
        ("len", ctypes.c_uint),
        ("buf", ctypes.c_char * 2048)
    ]


class procmsg(ctypes.Structure):
    _fields_ = [
        ("source", sourcetype),
        ("cmd", ctypes.c_int),
        ("timeout", ctypes.c_int),
        ("len", ctypes.c_uint),
        ("buf", ctypes.c_char * 2048)
    ]


class aeskeymsg(ctypes.Structure):
    _fields_ = [
        ("key_ascii", ctypes.c_char * 65),
        ("ivt_ascii", ctypes.c_char * 33)
    ]


class versions(ctypes.Structure):
    _fields_ = [
        ("minimum_version", ctypes.c_char * 256),
        ("maximum_version", ctypes.c_char * 256),
        ("current_version", ctypes.c_char * 256),
        ("update_type", ctypes.c_char * 256)
    ]


class revisions(ctypes.Structure):
    _fields_ = [
        ("boardname", ctypes.c_char * 256),
        ("revision", ctypes.c_char * 256)
    ]


class vars(ctypes.Structure):
    _fields_ = [
        ("varnamespace", ctypes.c_char * 256),
        ("varname", ctypes.c_char * 256),
        ("varvalue", ctypes.c_char * 256)
    ]


class msgdata(ctypes.Union):
    _fields_ = [
        ("msg", ctypes.c_char * 128),
        ("status", status),
        ("notify", notify),
        ("instmsg", instmsg),
        ("procmsg", procmsg),
        ("aeskeymsg", aeskeymsg),
        ("versions", versions),
        ("revisions", revisions),
        ("vars", vars)
    ]


class ipc_message(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_int),
        ("type", msgtype),
        ("data", msgdata)
    ]
