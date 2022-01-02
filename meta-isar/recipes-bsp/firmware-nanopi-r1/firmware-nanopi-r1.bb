# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# SPDX-License-Identifier: MIT

inherit dpkg-raw

DESCRIPTION = "Wi-Fi firmware suport for NanoPi R1"
MAINTAINER = "mtda-users <mtda-users@googlegroups.com>"
DEBIAN_DEPENDS = "firmware-brcm80211"

do_install() {
    targetdir=${D}/lib/firmware/brcm
    targetlnk=${targetdir}/brcmfmac43430-sdio.friendlyarm,nanopi-r1.txt
    install -m 0755 -d ${targetdir}
    ln -s brcmfmac43430-sdio.AP6212.txt ${targetlnk}
}
