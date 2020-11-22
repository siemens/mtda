# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "a4dfcdd64cfb4678418d86199e9e494affc58619"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
