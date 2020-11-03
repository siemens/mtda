# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "3c37a8f959c1129d00473c8a5c01b6e7c78605b2"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
