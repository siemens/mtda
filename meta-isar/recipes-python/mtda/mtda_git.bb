# This Isar layer is part of MTDA
# Copyright (C) 2017-2019 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI += "git://github.com/MentorEmbedded/mtda.git;protocol=https;branch=master"
SRCREV   = "77811d6e78c03d56e6d0a6864cf274ab9f007de3"
S        = "${WORKDIR}/git"

DEPENDS += "zerorpc-python"
