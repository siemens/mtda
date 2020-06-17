# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "50601574612553640cd6d5701d186c0944e89a22"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
