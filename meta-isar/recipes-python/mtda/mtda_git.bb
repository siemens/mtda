# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "ee20032ab2ebf1d96aafcbd180c6027da1cd6d0b"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
