from mtda.main import MultiTenantDeviceAccess
import os
import time
import uuid
import zerorpc

class Client:

    def __init__(self, host=None):
        agent = MultiTenantDeviceAccess()
        agent.load_config(host)
        if agent.remote is not None:
            uri = "tcp://%s:%d" % (agent.remote, agent.ctrlport)
            self._impl = zerorpc.Client(heartbeat=20)
            self._impl.connect(uri)
        else:
            self._impl = agent
        self._agent = agent
        self._session = os.getenv('MTDA_SESSION', str(uuid.uuid1()))

    def console_clear(self):
        return self._impl.console_clear(self._session)

    def console_flush(self):
        return self._impl.console_flush(self._session)

    def console_getkey(self):
        return self._agent.console_getkey()

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

    def console_remote(self, host):
        return self._agent.console_remote(host)

    def console_run(self, cmd):
        return self._impl.console_run(cmd, self._session)

    def console_send(self, data, raw=False):
        return self._impl.console_send(data, raw, self._session)

    def console_tail(self):
        return self._impl.console_tail(self._session)

    def power_locked(self):
        return self._impl.power_locked(self._session)

    def sd_bytes_written(self):
        return self._impl.sd_bytes_written(self._session)

    def sd_close(self):
        return self._impl.sd_close(self._session)

    def sd_locked(self):
        return self._impl.sd_locked(self._session)

    def sd_open(self):
        tries = 60
        while tries > 0:
            tries = tries - 1
            status = self._impl.sd_open(self._session)
            if status == True:
                return True
            time.sleep(1)
        return False

    def sd_status(self):
        return self._impl.sd_status(self._session)

    def sd_write_image(self, path, callback=None):
        # Get size of the (compressed) image
        imgname = os.path.basename(path)

        # Open the specified image
        try:
            st = os.stat(path)
            imgsize = st.st_size
            isBZ2 = path.endswith(".bz2")
            isGZ = path.endswith(".gz")
            image = open(path, "rb")
        except FileNotFoundError:
            return False

        # Open the SD card device
        status = self.sd_open()
        if status == False:
            image.close()
            return False

        # Copy loop
        data = image.read(self._agent.blksz)
        dataread = len(data)
        totalread = 0
        while totalread < imgsize:
            totalread += dataread

            # Report progress via callback
            if callback is not None:
                callback(imgname, totalread, imgsize)

            # Write block to SD card
            if isBZ2 == True:
                bytes_wanted = self._impl.sd_write_bz2(data, self._session)
            if isGZ == True:
                bytes_wanted = self._impl.sd_write_gz(data, self._session)
            else:
                bytes_wanted = self._impl.sd_write_raw(data, self._session)

            # Check what to do next
            if bytes_wanted < 0:
                # Handle read/write error
                image.close()
                self.sd_close()
                return False
            elif bytes_wanted > 0:
                # Read next block
                data = image.read(bytes_wanted)
                dataread = len(data)
            else:
                # Agent may continue without further data
                data = b''
                dataread = 0

        # Close the local image and SD card
        image.close()
        status = self.sd_close()
        return status

    def sd_to_host(self):
        return self._impl.sd_to_host(self._session)

    def sd_to_target(self):
        return self._impl.sd_to_target(self._session)

    def sd_toggle(self):
        return self._impl.sd_toggle(self._session)

    def start(self):
        return self._agent.start()

    def remote(self):
        return self._agent.remote

    def session(self):
        return self._session

    def target_lock(self, retries=0):
        status = False
        while status == False:
            status = self._impl.target_lock(self._session)
            if retries <= 0 or status == True:
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
