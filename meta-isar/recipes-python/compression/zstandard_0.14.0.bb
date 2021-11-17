# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2017-2021 Mentor Graphics, a Siemens business
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

inherit dpkg

SRC_URI = " \
    https://files.pythonhosted.org/packages/1b/a7/97b157508923ec0c2d27cdc23003cb096fa50ae38ded6e54adcbca3dca35/${PN}-${PV}.tar.gz \
    file://${PN}-${PV}/debian \
"

SRC_URI[sha256sum] = "9052398da52e8702cf9929999c8986b0f68b18c793e309cd8dff5cb7863d7652"
