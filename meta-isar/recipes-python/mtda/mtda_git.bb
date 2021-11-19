# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI += "git://git@github.com/siemens/mtda.git;protocol=ssh;branch=master"
SRCREV   = "f3ba1ef8fc7f8e4fab3dd35fbdd55e1b0ec2eeaa"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
