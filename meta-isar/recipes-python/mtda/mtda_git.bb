# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "a95ea889db776c2c57eeb818e243e633105a314b"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
