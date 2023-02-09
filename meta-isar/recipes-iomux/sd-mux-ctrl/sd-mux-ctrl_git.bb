# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI += "git://git.tizen.org/cgit/tools/testlab/sd-mux;protocol=https;branch=master"
SRCREV   = "204f4f2e7e02addabe2e221b3b6c7bb91997e2a2"
S        = "${WORKDIR}/git"
