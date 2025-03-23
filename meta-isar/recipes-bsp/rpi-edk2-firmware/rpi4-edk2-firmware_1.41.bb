# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (c) Siemens AG, 2025
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------
#
# The recipe provides the pre-built EDK2 firmware for the Raspberry Pi 4. The
# firmware is loaded by the RPi loader (start4.elf), loads the DTB and patches
# the overlays. Then, performs standard efi booting and passes the DTB infos
# as ACPI tables.

inherit dpkg-raw

DPKG_ARCH = "arm64"

SRC_URI = " \
    file://config.override.txt \
    https://github.com/pftf/RPi4/releases/download/v1.41/RPi4_UEFI_Firmware_v1.41.zip \
"
SRC_URI[sha256sum] = "d2a97e36665920dbb5a6aea200e48fc59b1e26cf94a478db7f57833118c2b64a"

DEBIAN_DEPENDS = "rpi-firmware"
RDEPENDS:${PN} += "rpi-firmware"

do_install[cleandirs] += "${D}/usr/lib/${BPN}"
do_install() {
    DST=${D}/usr/lib/${BPN}
    cat ${WORKDIR}/config.override.txt > ${WORKDIR}/config.txt
    install -m 0644 ${WORKDIR}/config.txt $DST
    install -m 0644 ${WORKDIR}/RPI_EFI.fd $DST
}

DEB_BUILD_OPTIONS += "nostrip"
