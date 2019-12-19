# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "2cc42adf1954d336c49ca89110efc6173cbab33e"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
