# ---------------------------------------------------------------------------
# MTDA Client
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2021 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------


import os
import random
import socket
import time
import zerorpc

from mtda.main import MultiTenantDeviceAccess
import mtda.constants as CONSTS


class Client:

    def __init__(self, host=None, session=None, config_files=None):
        agent = MultiTenantDeviceAccess()
        agent.load_config(host, config_files=config_files)
        if agent.remote is not None:
            uri = "tcp://%s:%d" % (agent.remote, agent.ctrlport)
            self._impl = zerorpc.Client(heartbeat=CONSTS.RPC.HEARTBEAT,
                                        timeout=CONSTS.RPC.TIMEOUT)
            self._impl.connect(uri)
        else:
            self._impl = agent
        self._agent = agent

        if session is None:
            HOST = socket.gethostname()
            USER = os.getenv("USER")
            WORDS = "/usr/share/dict/words"
            if os.path.exists(WORDS):
                WORDS = open(WORDS).read().splitlines()
                name = random.choice(WORDS)
                if name.endswith("'s"):
                    name = name.replace("'s", "")
            elif USER is not None and HOST is not None:
                name = "%s@%s" % (USER, HOST)
            else:
                name = "mtda"
            self._session = os.getenv('MTDA_SESSION', name)
        else:
            self._session = session

    def agent_version(self):
        return self._impl.agent_version()

    def config_set_session_timeout(self, timeout):
        return self._impl.config_set_session_timeout(timeout, self._session)

    def console_prefix_key(self):
        return self._agent.console_prefix_key()

    def command(self, args):
        return self._impl.command(args, self._session)

    def console_clear(self):
        return self._impl.console_clear(self._session)

    def console_dump(self):
        return self._impl.console_dump(self._session)

    def console_flush(self):
        return self._impl.console_flush(self._session)

    def console_getkey(self):
        return self._agent.console_getkey()

    def console_init(self):
        return self._agent.console_init()

    def console_head(self):
        return self._impl.console_head(self._session)

    def console_lines(self):
        return self._impl.console_lines(self._session)

    def console_locked(self):
        return self._impl.console_locked(self._session)

    def console_print(self, data):
        return self._impl.console_print(data, self._session)

    def console_prompt(self, newPrompt=None):
        return self._impl.console_prompt(newPrompt, self._session)

    def console_remote(self, host, screen):
        return self._agent.console_remote(host, screen)

    def console_run(self, cmd):
        return self._impl.console_run(cmd, self._session)

    def console_send(self, data, raw=False):
        return self._impl.console_send(data, raw, self._session)

    def console_toggle(self):
        return self._agent.console_toggle(self._session)

    def console_tail(self):
        return self._impl.console_tail(self._session)

    def console_wait(self, what, timeout=None):
        return self._impl.console_wait(what, timeout, self._session)

    def env_get(self, name):
        return self._impl.env_get(name, self._session)

    def env_set(self, name, value):
        return self._impl.env_set(name, value, self._session)

    def keyboard_write(self, data):
        return self._impl.keyboard_write(data, self._session)

    def monitor_remote(self, host, screen):
        return self._agent.monitor_remote(host, screen)

    def monitor_send(self, data, raw=False):
        return self._impl.monitor_send(data, raw, self._session)

    def monitor_wait(self, what, timeout=None):
        return self._impl.monitor_wait(what, timeout, self._session)

    def pastebin_api_key(self):
        return self._agent.pastebin_api_key()

    def pastebin_endpoint(self):
        return self._agent.pastebin_endpoint()

    def power_locked(self):
        return self._impl.power_locked(self._session)

    def storage_bytes_written(self):
        return self._impl.storage_bytes_written(self._session)

    def storage_close(self):
        return self._impl.storage_close(self._session)

    def storage_locked(self):
        return self._impl.storage_locked(self._session)

    def storage_mount(self, part=None):
        return self._impl.storage_mount(part, self._session)

    def storage_open(self):
        tries = 60
        while tries > 0:
            tries = tries - 1
            status = self._impl.storage_open(self._session)
            if status is True:
                return True
            time.sleep(1)
        return False

    def storage_status(self):
        return self._impl.storage_status(self._session)

    def _storage_write(self, image, imgname, imgsize, callback=None):
        # Copy loop
        bytes_wanted = 0
        data = image.read(self._agent.blksz)
        dataread = len(data)
        totalread = 0
        while totalread < imgsize:
            totalread += dataread

            # Report progress via callback
            if callback is not None:
                callback(imgname, totalread, imgsize)

            # Write block to shared storage device
            bytes_wanted = self._impl.storage_write(data, self._session)

            # Check what to do next
            if bytes_wanted < 0:
                break
            elif bytes_wanted > 0:
                # Read next block
                data = image.read(bytes_wanted)
                dataread = len(data)
            else:
                # Agent may continue without further data
                data = b''
                dataread = 0

        # Close the local image
        image.close()

        # Wait for background writes to complete
        while True:
            status, writing, written = self._impl.storage_status(self._session)
            if writing is False:
                break
            if callback is not None:
                callback(imgname, totalread, imgsize)
            time.sleep(0.5)

        # Storage may be closed now
        status = self.storage_close()

        # Provide final update to specified callback
        if status is True and callback is not None:
            callback(imgname, totalread, imgsize)

        # Make sure an error is reported if a write error was received
        if bytes_wanted < 0:
            status = False

        return status

    def storage_update(self, dest, src=None, callback=None):
        path = dest if src is None else src
        imgname = os.path.basename(path)
        try:
            st = os.stat(path)
            imgsize = st.st_size
            image = open(path, "rb")
        except FileNotFoundError:
            return False

        status = self._impl.storage_update(dest, 0, self._session)
        if status is False:
            image.close()
            return False

        self._impl.storage_compression(CONSTS.IMAGE.RAW.value, self._session)
        return self._storage_write(image, imgname, imgsize, callback)

    def storage_write_image(self, path, callback=None):
        # Get size of the (compressed) image
        imgname = os.path.basename(path)

        # Open the specified image
        try:
            st = os.stat(path)
            imgsize = st.st_size
            if path.endswith(".bz2"):
                compression = CONSTS.IMAGE.BZ2.value
            elif path.endswith(".gz"):
                compression = CONSTS.IMAGE.GZ.value
            elif path.endswith(".zst"):
                compression = CONSTS.IMAGE.ZST.value
            elif path.endswith(".xz"):
                compression = CONSTS.IMAGE.XZ.value
            else:
                compression = CONSTS.IMAGE.RAW.value
            self._impl.storage_compression(compression, self._session)
            image = open(path, "rb")
        except FileNotFoundError:
            return False

        # Open the shared storage device
        status = self.storage_open()
        if status is False:
            image.close()
            return False

        return self._storage_write(image, imgname, imgsize, callback)

    def storage_to_host(self):
        return self._impl.storage_to_host(self._session)

    def storage_to_target(self):
        return self._impl.storage_to_target(self._session)

    def storage_swap(self):
        return self._impl.storage_swap(self._session)

    def start(self):
        return self._agent.start()

    def stop(self):
        if self._agent.remote is not None:
            self._impl.close()
        else:
            self._agent.stop()

    def remote(self):
        return self._agent.remote

    def session(self):
        return self._session

    def target_lock(self, retries=0):
        status = False
        while status is False:
            status = self._impl.target_lock(self._session)
            if retries <= 0 or status is True:
                break
            retries = retries - 1
            time.sleep(60)
        return status

    def target_locked(self):
        return self._impl.target_locked(self._session)

    def target_off(self):
        return self._impl.target_off(self._session)

    def target_on(self):
        return self._impl.target_on(self._session)

    def target_status(self):
        return self._impl.target_status(self._session)

    def target_toggle(self):
        return self._impl.target_toggle(self._session)

    def target_unlock(self):
        return self._impl.target_unlock(self._session)

    def target_uptime(self):
        return self._impl.target_uptime(self._session)

    def toggle_timestamps(self):
        return self._impl.toggle_timestamps()

    def usb_find_by_class(self, className):
        return self._impl.usb_find_by_class(className, self._session)

    def usb_has_class(self, className):
        return self._impl.usb_has_class(className, self._session)

    def usb_off(self, ndx):
        return self._impl.usb_off(ndx, self._session)

    def usb_off_by_class(self, className):
        return self._impl.usb_off_by_class(className, self._session)

    def usb_on(self, ndx):
        return self._impl.usb_on(ndx, self._session)

    def usb_on_by_class(self, className):
        return self._impl.usb_on_by_class(className, self._session)

    def usb_ports(self):
        return self._impl.usb_ports(self._session)

    def usb_status(self, ndx):
        return self._impl.usb_status(ndx, self._session)

    def usb_toggle(self, ndx):
        return self._impl.usb_toggle(ndx, self._session)

    def version(self):
        return self._agent.version

    def video_url(self, host="", opts=None):
        if host == "":
            host = os.getenv("MTDA_REMOTE", "")
        return self._impl.video_url(host, opts)
