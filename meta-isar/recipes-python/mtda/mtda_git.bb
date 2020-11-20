# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "58a1240d6ca035bd34d627e9234533d5b6b69594"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
