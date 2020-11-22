# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "071d6cc7abbac3007c74fe950bf987efd6abef94"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
