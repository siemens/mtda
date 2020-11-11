# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "29bd89ce8dd51bb3307d49b9d401ee7228a87af6"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
