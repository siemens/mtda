# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI += "git://git@github.com/siemens/mtda.git;protocol=https;branch=master"
SRCREV   = "691b34267ae6204b5b33376ebaa1393d9b03c3a0"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
