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
SRC_URI[sha256sum] = "d72c8694b9352ea16fe3fae7475d712e8a13f30048f46274fd1d6ef920da3e67"

do_install() {
    mkdir -p ${D}/opt
    cp -r ${WORKDIR}/pyodide ${D}/opt/
}
