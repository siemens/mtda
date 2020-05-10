# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "93d436069059b5277364e42bd8fba65bc50e7958"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
