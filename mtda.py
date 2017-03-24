#!/usr/bin/env python3

# System imports
import daemon
import getopt
import os
import signal
import sys
import threading
import zerorpc

# Local imports
from mtda.main import MultiTenantDeviceAccess
import mtda.power.controller

class Application:

    def __init__(self):
        self.agent  = None
        self.console_rx_alive = False
        self.console_rx_thread = None
        self.remote = None

    def daemonize(self):
        context = daemon.DaemonContext(
            working_directory=os.getcwd(),
            stdout=open(self.logfile, 'w+'),
            stderr=open(self.logfile, 'w+'),
            umask=0o002,
            pidfile=lockfile.FileLock(self.pidfile)
        )

        context.signal_map = {
            signal.SIGTERM: 'terminate',
            signal.SIGHUP:  'terminate',
        }

        with context:
            self.server()

    def start_console_reader(self):
        self.console_rx_alive = True
        self.console_rx_thread = threading.Thread(target=self.console_reader, name='console_rx')
        self.console_rx_thread.daemon = True
        self.console_rx_thread.start()

    def console_reader(self):
        try:
            con = self.agent.console
            con.probe()
            while self.console_rx_alive == True:
                data = con.read(con.pending() or 1)
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
        except Exception:
            self.console_rx_alive = False
            print("read error on the console!", file=sys.stderr)

    def server(self):
        if self.agent.console is not None:
            self.start_console_reader()

        uri = "tcp://*:%d" % (self.agent.ctrlport)
        s = zerorpc.Server(self.agent)
        s.bind(uri)
        s.run()

    def client(self):
        if self.remote is not None:
            uri = "tcp://%s:%d" % (self.remote, self.agent.ctrlport)
            c = zerorpc.Client()
            c.connect(uri)
            return c
        else:
            return self.agent

    def target_cmd(self, args):
        if len(args) > 0:
            cmd = args[0]
            args.pop(0)
            if cmd == "off":
                self.client().target_off()
            elif cmd == "on":
                self.client().target_on()
            else:
                print("unknown target command '%s'!" %(cmd), file=sys.stderr)

    def main(self):
        daemonize = False
        detach = True

        options, stuff = getopt.getopt(sys.argv[1:], 
            'dnr:',
            ['daemon', 'no-detach', 'remote='])
        for opt, arg in options:
            if opt in ('-d', '--daemon'):
                daemonize = True
            if opt in ('-n', '--no-detach'):
                detach = False 
            if opt in ('-r', '--remote'):
                self.remote = arg

        # Create agent
        self.agent = MultiTenantDeviceAccess() 

        # Load default/specified configuration
        self.agent.load_config()

        # Start our server
        if daemonize == True:
            if detach == True:
                self.daemonize()
            else:
                self.server()

        # Check for non-option arguments
        if len(stuff) > 0:
           cmd = stuff[0]
           stuff.pop(0)

           cmds = {
              'target' : self.target_cmd
           } 

           if cmd in cmds:
               cmds[cmd](stuff)
           else:
               print("unknown command '%s'!" %(cmd), file=sys.stderr)
               sys.exit(1)

if __name__ == '__main__':
    app = Application()
    app.main()

