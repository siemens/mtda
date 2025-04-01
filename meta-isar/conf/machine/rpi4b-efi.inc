# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (c) Siemens AG, 2025
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

DISTRO_ARCH ?= "arm64"

KERNEL_NAME ?= "arm64"

IMAGE_FSTYPES ??= "wic"
WKS_FILE ??= "rpi4b-efi.wks"

IMAGER_BUILD_DEPS = "u-boot-config-rpi4b"
IMAGER_INSTALL:wic += "${IMAGER_BUILD_DEPS}"

IMAGE_EFI_BOOT_FILES = " \
    /usr/lib/u-boot-config-rpi4b/config.txt;config.txt \
    /usr/lib/u-boot/rpi_arm64/u-boot.bin;u-boot.bin \
    /usr/lib/rpi-firmware/fixup4.dat;fixup4.dat \
    /usr/lib/rpi-firmware/start4.elf;start4.elf \
    /usr/lib/rpi-firmware/overlays/*;overlays/ \
    ${IMAGE_ROOTFS}/usr/lib/linux-image-*/broadcom/bcm2711-rpi-4-b.dtb \
"

IMAGE_PREINSTALL:append = " firmware-brcm80211"
