# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "08ff44f8b1c5e5c052fdfc2bc12720df39f96e51"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
