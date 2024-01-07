# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2024 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

SRC_URI += "https://ftp.denx.de/pub/u-boot/u-boot-${PV}.tar.bz2"
SRC_URI[sha256sum] = "cde723e19262e646f2670d25e5ec4b1b368490de950d4e26275a988c36df0bd4"
S = "${WORKDIR}/u-boot-${PV}"
