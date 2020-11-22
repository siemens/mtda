# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "8e4eead856b953deabc640f14993587681e2883c"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
