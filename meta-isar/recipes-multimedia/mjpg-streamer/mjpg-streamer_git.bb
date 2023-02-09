# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI += "git://github.com/jacksonliam/mjpg-streamer;protocol=https;branch=master \
            file://git/mjpg-streamer-experimental/debian"
SRCREV   = "310b29f4a94c46652b20c4b7b6e5cf24e532af39"
S        = "${WORKDIR}/git/mjpg-streamer-experimental"
