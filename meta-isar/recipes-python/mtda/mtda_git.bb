# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "1cc1bffe702a2ffd52dc62423314064bb761e5d8"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
