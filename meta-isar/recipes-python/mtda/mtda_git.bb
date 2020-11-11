# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "1ba6410e298dc721aaebd9eda83c0ddbec4e1b3c"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
