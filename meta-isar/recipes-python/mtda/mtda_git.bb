# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "70fddfad89dc11c7cefd7bc2815009ab582ea9ea"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
