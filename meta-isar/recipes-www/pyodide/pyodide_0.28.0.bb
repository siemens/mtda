# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg-raw

PR = "1"
CHANGELOG_V = "${PV}-${PR}"

SRC_URI = "https://github.com/pyodide/pyodide/releases/download/${PV}/${PN}-${PV}.tar.bz2"
SRC_URI[sha256sum] = "e18c03ba17163d89b8d1529f384a8f7944884509750c301d5c451c32ecf353ba"

do_install() {
    mkdir -p ${D}/opt
    cp -r ${WORKDIR}/pyodide ${D}/opt/
}
