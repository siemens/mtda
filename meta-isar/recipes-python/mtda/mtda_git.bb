# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "530334becfcc182e115e2b491e7b1d5ab951a704"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
