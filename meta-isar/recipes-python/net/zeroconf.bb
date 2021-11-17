# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2017-2021 Mentor Graphics, a Siemens business
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

PV = "0.28.6"

SRC_URI = " \
    https://files.pythonhosted.org/packages/4f/90/f81ae501020cd920c7cd69bb0076fcb541347f7ed96b66b050107c7636f8/${PN}-${PV}.tar.gz \
    file://${PN}-${PV} \
"

SRC_URI[sha256sum] = "70f10f0f16e3a8c4eb5e1a106b812b8d052253041cf1ee1195933df706f5261c"
