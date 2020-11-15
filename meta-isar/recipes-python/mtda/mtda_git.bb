# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "fc36caac28043a7868a8ed7f74f591a4be68eca8"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
