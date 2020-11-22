# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "67c23d9852d3ca880c551c2ed2bcab788cba214c"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
