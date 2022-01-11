# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# SPDX-License-Identifier: MIT

DESCRIPTION        = "use /dev/mmcblk0 as device for our USB Mass Storage function"
MAINTAINER         = "Cedric Hombourger <cedric.hombourger@siemens.com>"
SRC_URI            = "file://usb-functions file://10-after-mmcblk0.conf"
FILESPATH_prepend := "${THISDIR}/${PN}:"
DPKG_ARCH          = "all"

inherit dpkg-raw

do_install() {
    cd ${WORKDIR}
    install -m 0755 -d            ${D}/etc/mtda/
    install -m 0644 usb-functions ${D}/etc/mtda/
    install -m 0755 -d            ${D}/lib/systemd/system/mtda-usb-functions.service.d/
    install -m 0644 *.conf        ${D}/lib/systemd/system/mtda-usb-functions.service.d/
}
