# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

require u-boot.inc
require u-boot-${PV}.inc

U_BOOT_BIN = "u-boot-sunxi-with-spl.bin"
U_BOOT_CONFIG = "nanopi_r1_defconfig"

SRC_URI += "file://add-nanopi-r1.patch"
