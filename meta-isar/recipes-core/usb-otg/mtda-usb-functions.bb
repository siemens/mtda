# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# SPDX-License-Identifier: MIT

inherit dpkg-raw

DESCRIPTION        = "USB functions for MTDA"
HOMEPAGE           = "https://github.com/siemens/mtda"
LICENSE            = "MIT"
MAINTAINER         = "Cedric Hombourger <cedric.hombourger@siemens.com>"
PV                 = "0.5"
FILESPATH_prepend := "${THISDIR}/${PN}:"
DEBIAN_DEPENDS     = "python3"
DPKG_ARCH          = "all"
SRC_URI            = "file://mtda-usb-functions.service \
                      file://postinst                   \
                      file://usb-functions              "

do_install() {
    cd ${WORKDIR}
    install -m 0755 -d                         ${D}/lib/systemd/system/
    install -m 0644 mtda-usb-functions.service ${D}/lib/systemd/system/
    install -m 0755 -d                         ${D}/usr/libexec/mtda/
    install -m 0755 usb-functions              ${D}/usr/libexec/mtda/
}
