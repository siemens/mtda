# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI = "https://github.com/stefanberger/${PN}/archive/refs/tags/v${PV}.tar.gz \
           file://nocheck.patch"
SRC_URI[sha256sum] = "bed41871ad42ec852c450f5764be36b6c16456b943b912351eca9c29ce382976"

DEPENDS = "libtpms"

dpkg_runbuild_prepend() {
    export DEB_BUILD_OPTIONS=nocheck
}
