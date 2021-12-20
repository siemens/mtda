# ---------------------------------------------------------------------------
# This Isar layer is part of MTDA
# Copyright (C) 2021 Siemens Digital Industries Software
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# additional .list files may be provided in local.conf
MTDA_EXTRA_APT_SOURCES ??= ""

# custom apt preferences may also be used
MTDA_EXTRA_APT_PREFERENCES ??= ""

# make Isar use our custom settings
DISTRO_APT_SOURCES_append = " ${MTDA_EXTRA_APT_SOURCES}"
DISTRO_APT_PREFERENCES_append = " ${MTDA_EXTRA_APT_PREFERENCES}"
