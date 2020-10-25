# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "5b2b8e6dda918d97d1ade5ed06f059e2f533e983"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
