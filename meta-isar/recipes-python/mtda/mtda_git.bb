# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "3f9c563d8aca42c265a3d7db41844b8839c2ae76"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
