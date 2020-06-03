# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "5a6e486fa024fbd15c256628be98aeadf384326f"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
