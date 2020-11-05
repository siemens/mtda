# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "9c011372b8d126c99bc9e205689087d9b3b3b61e"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
