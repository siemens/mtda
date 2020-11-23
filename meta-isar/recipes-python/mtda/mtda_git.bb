# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "d30c5385e2ddea3bc3b201207a45aded929fc5b4"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
