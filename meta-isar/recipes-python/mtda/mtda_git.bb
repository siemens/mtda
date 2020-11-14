# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "a193766a82ba577705e023f2e85fe39d03e0b6a6"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
