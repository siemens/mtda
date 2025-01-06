# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI = " \
    https://files.pythonhosted.org/packages/73/ff/d61ef9f5d10e671421d1368e87d3525325483ebd7da262b1d3087443662b/zerorpc-${PV}.tar.gz \
    file://0001-gevent_zmq-import-enums-from-pyzmq-23.0.0.patch \
    file://0002-do-not-use-future.patch \
    file://zerorpc-${PV}/debian \
"

PR = "6"
S = "${WORKDIR}/zerorpc-${PV}"
SRC_URI[sha256sum] = "d2ee247a566fc703f29c277d767f6f61f1e12f76d0402faea4bd815f32cbf37f"
