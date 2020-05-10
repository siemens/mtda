# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "ee13dab2d5331d623d4f8bd764268ee48c974b57"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
