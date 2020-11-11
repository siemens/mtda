# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "3839aa45d29abdcc1c8333c3ee088f1aa569ec3c"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
