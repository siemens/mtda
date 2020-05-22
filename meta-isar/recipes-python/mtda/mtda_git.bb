# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "64906560dd9d09071811f31ef1f59a02bdb11225"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
