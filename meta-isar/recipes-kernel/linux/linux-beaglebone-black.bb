# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2022 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

require recipes-kernel/linux/linux-custom.inc

SRC_URI += "git://github.com/beagleboard/linux.git;protocol=https;branch=5.10"
SRCREV = "${AUTOREV}"
S = "${WORKDIR}/git"

KERNEL_DEFCONFIG = "ti_sdk_am3x_release_defconfig"
