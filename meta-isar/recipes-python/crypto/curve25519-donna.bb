# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

PV = "1.3"

SRC_URI = " \
    https://files.pythonhosted.org/packages/01/05/1ab1cc54c2b1e933721b8e65fedc01098e6b8ffdccedbc4a682d4e0db8c1/${PN}-${PV}.tar.gz \
    file://${PN}-${PV}/debian \
"

SRC_URI[sha256sum] = "1818a9d5356a05c022cd504f44fe1d2f641a5c020f8a4c51b2294e02bd9c1bf0"
