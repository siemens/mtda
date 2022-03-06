# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (c) Siemens AG, 2020-2022
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI = " \
    https://github.com/raspberrypi/firmware/archive/${PV}.tar.gz;downloadfilename=${PN}-${PV}.tar.gz \
    file://debian \
    file://rules"
SRC_URI[sha256sum] = "67c49b6f2fbf4ee612536b3fc24e44ab3fa9584c78224865699f1cbc1b8eea3c"

S = "${WORKDIR}/firmware-${PV}"

DEBIAN_BUILD_DEPENDS = "device-tree-compiler"

do_prepare_build[cleandirs] += "${S}/debian"
do_prepare_build() {
    cp -r ${WORKDIR}/debian ${S}

    deb_debianize
}
