# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "8268a17e417a9c26cd1d8cbb2b0da8b9a418c754"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
