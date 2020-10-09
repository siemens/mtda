# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "5a9dd8fd603019b18fd6e1b4c964a98adc82c770"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
