# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "1b51a542d72cf3ba982ce8da4625e019e2ded0b9"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
