# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "f0b8efcf1813c13de530d4bd7eb07ed4785f7e94@
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
