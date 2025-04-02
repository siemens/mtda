# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

SWU_SIGNED = "0"

require recipes-core/images/efibootguard.inc
require recipes-core/images/swupdate.inc
require recipes-core/images/mtda-image.bb

# get a hostname via DHCP
IMAGE_INSTALL:remove = "mtda-hostname"
