# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "62524f0ac5611fe2ea9921dc6009c399a365c029"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
