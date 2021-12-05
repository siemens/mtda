# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI = "https://github.com/stefanberger/${PN}/archive/refs/tags/v${PV}.tar.gz"
SRC_URI[sha256sum] = "9a4d1ed07b78142c394faad1a1481771d470048f5859e80593fe42c82e5635a5"

DEPENDS = "gnutls28"
