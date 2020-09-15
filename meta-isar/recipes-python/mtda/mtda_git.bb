# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "eb384b1a65d7b46de79e385aff9a3529b2ef7eae@
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
