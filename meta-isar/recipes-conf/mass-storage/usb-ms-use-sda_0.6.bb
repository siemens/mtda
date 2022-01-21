# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# SPDX-License-Identifier: MIT

DESCRIPTION        = "use /dev/sda as device for our USB Mass Storage function"
MAINTAINER         = "Cedric Hombourger <cedric.hombourger@siemens.com>"
SRC_URI            = "file://10-after-sda.conf"
FILESPATH_prepend := "${THISDIR}/${PN}:"
DPKG_ARCH          = "all"

inherit dpkg-raw

do_install() {
    cd ${WORKDIR}
    install -m 0755 -d     ${D}/lib/systemd/system/mtda.service.d/
    install -m 0644 *.conf ${D}/lib/systemd/system/mtda.service.d/
}
