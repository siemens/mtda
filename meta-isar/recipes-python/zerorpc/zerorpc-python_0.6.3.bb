# This Isar layer is part of MTDA
# Copyright (C) 2017-2020 Mentor Graphics, a Siemens business

inherit dpkg

SRC_URI = " \
    https://files.pythonhosted.org/packages/73/ff/d61ef9f5d10e671421d1368e87d3525325483ebd7da262b1d3087443662b/zerorpc-${PV}.tar.gz \
    file://zerorpc-${PV}/debian \
"

S = "${WORKDIR}/zerorpc-${PV}"
SRC_URI[sha256sum] = "d2ee247a566fc703f29c277d767f6f61f1e12f76d0402faea4bd815f32cbf37f"
