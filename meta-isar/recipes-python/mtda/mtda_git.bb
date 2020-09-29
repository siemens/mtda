# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "73d05b0e52be135cce0846b82793bbc22a309f6c"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
