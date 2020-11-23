# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "59236510dc5acce56df673e58bff721cd147e3c4"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
