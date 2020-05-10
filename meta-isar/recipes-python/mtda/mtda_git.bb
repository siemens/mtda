# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "c969a49fbab90c5cd9ebc9044e0dd139314b0766"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
