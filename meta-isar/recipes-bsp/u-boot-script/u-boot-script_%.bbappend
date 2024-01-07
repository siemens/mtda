# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2024 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# Suffix the u-boot-script package to get unique packages in our binary feeds
PN .= "-${DISTRO}-${MACHINE}"
