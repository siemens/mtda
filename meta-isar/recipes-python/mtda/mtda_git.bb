# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "ec6c1b2451bb2aea97bafd691896057b09a4f3f1"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
