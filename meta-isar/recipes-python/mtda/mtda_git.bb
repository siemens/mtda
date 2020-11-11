# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "6312f807540e32eac7f91ab320fd70276904f67b"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
