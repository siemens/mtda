# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "6bcfd7d42f2804fa1cb86daa8d3489ee00a4d262"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
