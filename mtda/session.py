# ---------------------------------------------------------------------------
# Session Manager for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2024 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import time
import threading

import mtda.constants as CONSTS


class SessionManager:
    def __init__(self, mtda, lock_timeout, session_timeout):
        self.mtda = mtda
        self._lock = threading.Lock()
        self._lock_owner = None
        self._lock_expiry = None
        self._lock_timeout = lock_timeout
        self._session_timeout = session_timeout
        self._monitors = [mtda]
        self._timer = None
        self._sessions = {}

    def check(self, session=None):
        self.mtda.debug(3, f"session.check({session})")

        events = []
        now = time.monotonic()
        result = None

        with self._lock:
            # Register new session
            if session is not None:
                if session not in self._sessions:
                    events.append(f"{CONSTS.SESSION.ACTIVE} {session}")
                self._sessions[session] = now + self._session_timeout

            # Check for inactive sessions
            inactive = []
            for s in self._sessions:
                left = self._sessions[s] - now
                self.mtda.debug(3, "session %s: %d seconds" % (s, left))
                if left <= 0:
                    inactive.append(s)
            for s in inactive:
                events.append(f"{CONSTS.SESSION.INACTIVE} {s}")
                self._sessions.pop(s, "")
                # Check if this was the last session so we tell monitors when
                # the last session is removed (and do not repeat that event
                # unlike the RUNNING event that we want to periodically send)
                if len(self._sessions) == 0:
                    events.append(f"{CONSTS.SESSION.NONE}")

            if len(self._sessions) > 0:
                # There are active sessions: let monitors know
                events.append(f"{CONSTS.SESSION.RUNNING}")

            # Release device if the session owning the lock is idle
            if self._lock_owner is not None:
                if session == self._lock_owner:
                    self._lock_expiry = now + self._lock_timeout
                elif now >= self._lock_expiry:
                    events.append(f"UNLOCKED {self._lock_owner}")
                    self._lock_owner = None

        # Send event sessions generated above
        for e in events:
            self.notify(e)

        self.mtda.debug(3, f"session.check: {result}")
        return result

    def lock(self, session):
        self.mtda.debug(3, f"session.lock({session})")

        self.check(session)
        with self._lock:
            if self._lock_owner is None:
                self._lock_owner = session
                self.notify(f"LOCKED {session}")
                result = True
            else:
                result = False

        self.mtda.debug(3, f"session.lock(): {result}")
        return result

    def locked(self, session):

        self.check(session)
        with self._lock:
            result = self._lock_owner

        return result

    def unlock(self, session):
        self.mtda.debug(3, f"session.unlock({session})")

        result = False
        self.check(session)
        with self._lock:
            if self._lock_owner == session:
                self._lock_owner = None
                result = True

        if result is True:
            self.notify(f"UNLOCKED {session}")

        self.mtda.debug(3, f"session.unlock: {result}")
        return result

    def notify(self, info):
        self.mtda.debug(3, f"session.notify({info})")

        result = None
        if info is not None:
            for m in self._monitors:
                m.session_event(info)
            self.mtda.notify(CONSTS.EVENTS.SESSION, info)

        self.mtda.debug(3, f"session.notify: {result}")
        return result

    def monitor(self, monitor):
        self.mtda.debug(3, "session.monitor()")

        result = None
        with self._lock:
            self._monitors.append(monitor)

        self.mtda.debug(3, f"session.monitor: {result}")
        return result

    def set_timeout(self, timeout, session=None):
        self.mtda.debug(3, f"session.set_timeout({timeout}, {session})")

        with self._lock:
            result = self._session_timeout
            self._session_timeout = timeout
            now = time.monotonic()
            for s in self._sessions:
                left = self._sessions[s] - now
                if left > timeout:
                    self._sessions[s] = now + timeout
        self.check(session)

        self.mtda.debug(3, f"session.set_timeout: {result}")
        return result
