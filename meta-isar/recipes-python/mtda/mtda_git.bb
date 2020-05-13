# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "46f58a01ec45675e730f3b833eae8756f0ea6e97"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
