# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "dbfd2416a50947767d976d464ab5632b9b5b6b5a"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python zstandard"
