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
SRC_URI[sha256sum] = "4981021b82f600f450d64d9b82034dc603bf5429889a3947b2863e01992a343c"

S = "${WORKDIR}/firmware-${PV}"

DEBIAN_BUILD_DEPENDS = "device-tree-compiler"

do_prepare_build[cleandirs] += "${S}/debian"
do_prepare_build() {
    cp -r ${WORKDIR}/debian ${S}

    deb_debianize
}
