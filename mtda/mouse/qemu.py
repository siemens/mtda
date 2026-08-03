# ---------------------------------------------------------------------------
# QEMU mouse driver for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2026 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

# Local imports
from mtda.mouse.controller import MouseController
import mtda.constants as CONSTS

# bit0=left, bit1=right, bit2=middle
BUTTONS = (
    (1, "left"),
    (2, "right"),
    (4, "middle"),
)


class QemuController(MouseController):

    def __init__(self, mtda):
        self.mtda = mtda
        self.qemu = mtda.power
        self._index = None

    def configure(self, conf):
        self.mtda.debug(3, "mouse.qemu.configure()")
        return True

    def probe(self):
        self.mtda.debug(3, "mouse.qemu.probe()")

        result = (self.qemu is not None and self.qemu.variant == "qemu")
        if result is False:
            self.mtda.debug(1, "mouse.qemu.probe(): "
                               "a qemu power controller is required")

        self.mtda.debug(3, f"mouse.qemu.probe(): {str(result)}")
        return result

    def idle(self):
        return True

    def _tablet_state(self):
        """Return (index, active) for the "-device usb-tablet" device.
        The index is cached after the first successful lookup since
        the device set is fixed at boot, but "active" is read fresh
        every time: it reflects which pointer QEMU currently uses.
        """
        mice = self.qemu.qmp("query-mice")
        for mouse in (mice if mice is not None else []):
            if self._index is None:
                if "tablet" in mouse.get("name", "").lower():
                    self._index = mouse.get("index")
                else:
                    continue
            if mouse.get("index") == self._index:
                return self._index, mouse.get("current", False)

        return self._index, False

    def move(self, x, y, buttons=0):
        self.mtda.debug(3, f"mouse.qemu.move({x}, {y}, {buttons})")

        index, active = self._tablet_state()
        if index is not None:
            if active is False:
                self.qemu.qmp(
                        "human-monitor-command",
                        {"command-line": f"mouse_set {index}"})
        else:
            self.mtda.debug(1, "mouse.qemu.move(): "
                               "usb-tablet not found in 'query-mice'")

        ax = int(x * CONSTS.MOUSE.MAX_X)
        ay = int(y * CONSTS.MOUSE.MAX_Y)
        self.mtda.debug(3, "mouse.qemu.move(): "
                           f"ax={ax} ay={ay} buttons={buttons}")
        events = [
            {"type": "abs", "data": {"axis": "x", "value": ax}},
            {"type": "abs", "data": {"axis": "y", "value": ay}},
        ]
        for bit, button in BUTTONS:
            data = {"down": bool(buttons & bit), "button": button}
            events.append({"type": "btn", "data": data})
        result = self.qemu.qmp("input-send-event", {"events": events})

        self.mtda.debug(3, f"mouse.qemu.move(): {result}")
        return result


def instantiate(mtda):
    return QemuController(mtda)
