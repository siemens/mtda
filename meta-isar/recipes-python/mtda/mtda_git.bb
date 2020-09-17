# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "72d89674d85e4e29ec8cb3e9ea5ca838603e641e"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
