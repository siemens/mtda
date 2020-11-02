# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "09b934e2b6fb2200fa8a9cd98e4ffd3bec9218a2"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
