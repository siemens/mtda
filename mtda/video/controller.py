# ---------------------------------------------------------------------------
# Video interface for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (c) Mentor, a Siemens business, 2017-2021
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import abc


class VideoController(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def configure(self, conf):
        """ Configure this video controller from the provided
            configuration"""
        return

    @abc.abstractmethod
    def probe(self):
        """ Check presence of the video controller"""
        return

    @abc.abstractmethod
    def start(self):
        """ Start video capture """
        return False

    @abc.abstractmethod
    def stop(self):
        """ Stop video capture """
        return False

    @abc.abstractmethod
    def url(self, host=""):
        """ URL for the video stream """
        return None
