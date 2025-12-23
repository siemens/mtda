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
SRC_URI[sha256sum] = "85395f34a808cc8852f3c4a5f5d47f906a8a52fa05e5cd70da33be82f4d86a58"

do_install() {
    mkdir -p ${D}/opt
    cp -r ${WORKDIR}/pyodide ${D}/opt/
}
