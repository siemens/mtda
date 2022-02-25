# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2022 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI += "git://git@github.com/siemens/mtda.git;protocol=https;branch=master"
SRCREV   = "f42a025de754032d83e703ddd056f184982fbaa2"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
