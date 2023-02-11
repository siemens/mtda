# This Isar layer is part of MTDA
# Copyright (c) 2023 Siemens AG
# SPDX-License-Identifier: MIT

DESCRIPTION = "inject mtda binary package feeds into runtime image"

MTDA_APT_URI ??= "https://apt.fury.io/mtda/"

inherit dpkg-raw

DPKG_ARCH = "all"

SRC_URI = "file://postinst.tmpl"

TEMPLATE_FILES = "postinst.tmpl"
TEMPLATE_VARS = "MTDA_APT_URI"
