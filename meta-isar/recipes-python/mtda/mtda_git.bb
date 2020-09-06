# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "d90042bee6f0b78a15846eb9c1d5b17c8f1fe8dd"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
