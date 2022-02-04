# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2022 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI += "git://git@github.com/siemens/mtda.git;protocol=https;branch=master"
SRCREV   = "${AUTOREV}"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
