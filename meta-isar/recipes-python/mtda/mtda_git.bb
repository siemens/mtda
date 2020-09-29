# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "3aa1cdb749f5d6842fdfe9216d5a39a0efbf9dc8"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
