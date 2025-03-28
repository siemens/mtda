# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (c) Siemens AG, 2025
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg-raw

SRC_URI = "file://config.txt"

DESCRIPTION = "Raspberry Pi config to boot using U-Boot EFI"
MAINTAINER = "mtda-users <mtda-users@googlegroups.com>"

DPKG_ARCH = "arm64"
DEBIAN_DEPENDS = "rpi-firmware, u-boot-rpi"
RDEPENDS:${PN} += "rpi-firmware"

do_install[cleandirs] += "${D}/usr/lib/${BPN}"
do_install() {
    DST=${D}/usr/lib/${BPN}
    install -m 0644 ${WORKDIR}/config.txt $DST
}
