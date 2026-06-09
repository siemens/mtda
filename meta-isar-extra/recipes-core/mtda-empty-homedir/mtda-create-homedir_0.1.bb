# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2026 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg-raw

DESCRIPTION = "create mtda homedir if not present"
MAINTAINER = "mtda-users <mtda-users@googlegroups.com>"

SRC_URI = "file://${BPN}.tmpfiles"

do_prepare_build:append() {
    cp ${WORKDIR}/${BPN}.tmpfiles ${S}/debian/
}
