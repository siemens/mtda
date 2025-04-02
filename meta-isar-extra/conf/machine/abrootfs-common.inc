# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

SWUPDATE_BOOTLOADER ?= "efibootguard"
SWU_EFI_BOOT_DEVICE ?= "/dev/disk/by-uuid/2321-DCBA"
INITRAMFS_INSTALL += " \
    initramfs-squashfs-hook \
    initramfs-abrootfs-hook \
"
IMAGE_TYPEDEP:wic += "squashfs"
IMAGE_FSTYPES += "swu"

# the squashfs is already compressed. Do not compress externally
SWU_COMPRESSION_TYPE = ""
# compress the initrd with zstd to speedup decompression
INITRAMFS_PREINSTALL += "zstd"
