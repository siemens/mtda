# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg-raw

DESCRIPTION        = "USB functions for MTDA"
HOMEPAGE           = "https://mentor.com/"
LICENSE            = "MIT"
MAINTAINER         = "Mentor Embedded <embedded_support@mentor.com>"
PV                 = "0.3"
FILESPATH_prepend := "${THISDIR}/${PN}:"
DEBIAN_DEPENDS     = "python3"
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
