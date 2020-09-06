# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "a12e2ab47a7e0a357e49589522cae69d54e64973"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
