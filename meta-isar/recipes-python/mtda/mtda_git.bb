# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "a67bd559b128a5a286dcf88d44509d992da9dffe"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
