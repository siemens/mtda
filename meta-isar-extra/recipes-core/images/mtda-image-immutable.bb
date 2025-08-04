# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2025 Siemens AG
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# On trixie, swu signing is mandatory. We currently sign with the
# snakeoil keys. If needed, custom keys can be selected as well.
SWU_SIGNED = "1"

require recipes-core/images/efibootguard.inc
require recipes-core/images/swupdate.inc
require recipes-core/images/mtda-image.bb

# get a hostname via DHCP
IMAGE_INSTALL:remove = "mtda-hostname"

# register with WFX backend
IMAGE_INSTALL += "swupdate-config-wfx"
