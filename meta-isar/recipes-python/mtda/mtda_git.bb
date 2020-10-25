# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "d295521c2affe9d1c351aa7dd77cc1d24b2e49f7"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
