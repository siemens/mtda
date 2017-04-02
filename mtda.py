#!/usr/bin/env python3

# System imports
import daemon
import getopt
import lockfile
import os
import signal
import sys
import zerorpc

# Local imports
from mtda.main import MentorTestDeviceAgent
import mtda.power.controller

class Application:

    def __init__(self):
        self.agent  = None
        self.remote = None
        self.logfile = "/var/log/mtda.log"
        self.pidfile = "/var/run/mtda.pid"

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

    def server(self):
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

    def console_head(self, args):
        line = self.client().console_head()
        if line is not None:
            sys.stdout.write(line)
            sys.stdout.flush()

    def console_cmd(self, args):
        if len(args) > 0:
            cmd = args[0]
            args.pop(0)

            cmds = {
               'head' : self.console_head
            }

            if cmd in cmds:
                cmds[cmd](args)
            else:
                print("unknown console command '%s'!" %(cmd), file=sys.stderr)

    def target_off(self):
        self.client().target_off()

    def target_on(self):
        self.client().target_off()

    def target_cmd(self, args):
        if len(args) > 0:
            cmd = args[0]
            args.pop(0)

            cmds = {
               'off' : self.target_off,
               'on'  : self.target_on
            }

            if cmd in cmds:
                cmds[cmd](args)
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
        self.agent = MentorTestDeviceAgent() 

        # Load default/specified configuration
        self.agent.load_config(self.remote is not None)

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
              'console' : self.console_cmd,
              'target'  : self.target_cmd
           } 

           if cmd in cmds:
               cmds[cmd](stuff)
           else:
               print("unknown command '%s'!" %(cmd), file=sys.stderr)
               sys.exit(1)

if __name__ == '__main__':
    app = Application()
    app.main()

