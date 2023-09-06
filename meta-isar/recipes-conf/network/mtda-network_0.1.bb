# This Isar layer is part of MTDA
# Copyright (C) 2023 Siemens AG
# SPDX-License-Identifier: MIT

DESCRIPTION = "MTDA network configuration using network-manager"
MAINTAINER = "Cedric Hombourger <chombourger@gmail.com>"
DEBIAN_DEPENDS = "network-manager"
DPKG_ARCH = "all"

SRC_URI = "file://90-systemd-networkd-disabled.preset"

inherit dpkg-raw

do_install() {
    # disable systemd-networkd service
    install -d -m 755 ${D}/etc/systemd/system-preset
    install -m 755 ${WORKDIR}/90-systemd-networkd-disabled.preset ${D}/etc/systemd/system-preset/
}
