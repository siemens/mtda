# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "97de433648c0076253f3acac217f2ea37e959579"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
