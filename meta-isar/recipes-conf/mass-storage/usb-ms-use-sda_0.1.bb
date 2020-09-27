# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

DESCRIPTION        = "use /dev/sda as device for our USB Mass Storage function"
MAINTAINER         = "Cedric Hombourger <cedric_hombourger@mentor.com>"
SRC_URI            = "file://usb-functions"
FILESPATH_prepend := "${THISDIR}/${PN}:"

inherit dpkg-raw

do_install() {
    cd ${WORKDIR}
    install -m 0755 -d            ${D}/etc/mtda/
    install -m 0644 usb-functions ${D}/etc/mtda/
}
