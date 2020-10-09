# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "8d3a2da2b47d2130e9e0087f1a816c997ad26464"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
