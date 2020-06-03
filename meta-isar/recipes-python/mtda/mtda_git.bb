# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "acb5b8ca187c4c5e53489bf938fbb02e5ba6edc7"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
