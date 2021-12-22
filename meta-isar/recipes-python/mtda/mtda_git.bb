# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI += "git://git@github.com/siemens/mtda.git;protocol=https;branch=master"
SRCREV   = "514d28e7b3d141d453a10c2fb25b9fc22d53364d"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
