# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "f4d0b7c2272e96a7708766290fa259adeef1dd87"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
