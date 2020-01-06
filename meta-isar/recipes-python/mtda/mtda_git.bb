# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "cfb12b50c79eec7d5ed27782c8afbdd0c97f1968"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
