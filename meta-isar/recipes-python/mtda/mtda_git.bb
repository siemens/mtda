# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "fc9f1284667c895936cb8d39ff5b1e7584293311"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
