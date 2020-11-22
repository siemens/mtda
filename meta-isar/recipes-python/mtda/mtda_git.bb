# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "cd7243e909b2cb4a58ffe31bdb033f81de6c4cfb"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
