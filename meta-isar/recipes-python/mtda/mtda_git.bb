# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "5738e2b3df8160886e5d2a07f933878761ff4a4f"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
