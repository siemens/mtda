# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "28f51825807eec83f1659eed865e73d777237a25"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
