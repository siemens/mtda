# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

PV = "1.5"

SRC_URI = " \
    https://files.pythonhosted.org/packages/58/38/72ec85c953b90552fb015f31248256ef19e89a164a40ff8fef680259a608/${PN}-${PV}.tar.gz \
    file://${PN}-${PV}/debian \
"

SRC_URI[sha256sum] = "02053ee019ceef0df97294be2d4d5a8fc120fc86e81e08bec1245fc0f9403358"
