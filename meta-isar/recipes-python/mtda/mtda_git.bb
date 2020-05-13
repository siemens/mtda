# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "d6242ea95eef1cbe4aca87019bbf9930e8777bc8"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
