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
        self.exiting = False

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
        # Start our agent
        self.agent.start()

        # Start our RPC server
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

    def console_clear(self, args):
        self.client().console_clear()

    def console_flush(self, args):
        data = self.client().console_flush()
        if data is not None:
            sys.stdout.write(data)
            sys.stdout.flush()

    def console_head(self, args):
        line = self.client().console_head()
        if line is not None:
            sys.stdout.write(line)
            sys.stdout.flush()
    
    def console_lines(self, args):
        lines = self.client().console_lines()
        sys.stdout.write("%d\n" % (lines))
        sys.stdout.flush()

    def console_interactive(self, args=None):
        client = self.agent
        server = self.client()
        client.console_remote(self.remote)
        while self.exiting == False:
            c = client.console_getkey()
            if c == '\x01':
                c = client.console_getkey()
                self.console_menukey(c)
            else:
                server.console_send(c)

    def console_menukey(self, c):
        server = self.client()
        if c == 'p':
            server.target_toggle()
        elif c == 'q':
            self.exiting = True
        elif c == 't':
            server.toggle_timestamps()
        elif c == 'u':
            server.usb_toggle(1)

    def console_run(self, args):
        data = self.client().console_run(args[0])
        if data is not None:
            sys.stdout.write(data)
            sys.stdout.flush()

    def console_send(self, args):
        self.client().console_send(args[0])

    def console_tail(self, args):
        line = self.client().console_tail()
        if line is not None:
            sys.stdout.write(line)
            sys.stdout.flush()

    def console_help(self, args=None):
       print("The 'console' command accepts the following sub-commands:")
       print("   clear         Clear any data present in the console buffer")
       print("   flush         Flush content of the console buffer")
       print("   head          Fetch and print the first line from the console buffer")
       print("   interactive   Open the device console for interactive use")
       print("   lines         Print number of lines present in the console buffer")
       print("   run           Run the specified command via the device console")
       print("   send          Send characters to the device console")
       print("   tail          Fetch and print the last line from the console buffer")

    def console_cmd(self, args):
        if len(args) > 0:
            cmd = args[0]
            args.pop(0)

            cmds = {
               'clear'       : self.console_clear,
               'flush'       : self.console_flush,
               'head'        : self.console_head,
               'interactive' : self.console_interactive,
               'lines'       : self.console_lines,
               'run'         : self.console_run,
               'send'        : self.console_send,
               'tail'        : self.console_tail
            }

            if cmd in cmds:
                cmds[cmd](args)
            else:
                print("unknown console command '%s'!" %(cmd), file=sys.stderr)

    def help_cmd(self, args=None):
        if args is not None and len(args) > 0:
            cmd = args[0]
            args.pop(0)

            cmds = {
               'console' : self.console_help,
               'target'  : self.target_help
            }

            if cmd in cmds:
                cmds[cmd](args)
            else:
                print("no help found for command '%s'!" %(cmd), file=sys.stderr)
        else:
            print("usage: mtda [options] <command> [<args>]")
            print("")
            print("The most commonly used mtda commands are:")
            print("   console   Interact with the device console")
            print("   target    Power control the device")
            print("   usb       Control USB devices attached to the device")
            print("")

    def target_help(self, args=None):
       print("The 'target' command accepts the following sub-commands:")
       print("   on   Power on the device")
       print("   off  Power off the device")

    def target_off(self, args=None):
        self.client().target_off()

    def target_on(self, args=None):
        self.client().target_on()

    def target_toggle(self, args=None):
        self.client().target_toggle()

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
        self.agent.load_config(self.remote is not None, daemonize)

        # Start our server
        if daemonize == True:
            if detach == True:
                self.daemonize()
            else:
                self.server()
        else:
            # Start our agent
            self.agent.start()

        # Check for non-option arguments
        if len(stuff) > 0:
           cmd = stuff[0]
           stuff.pop(0)

           cmds = {
              'console' : self.console_cmd,
              'help'    : self.help_cmd,
              'target'  : self.target_cmd
           } 

           if cmd in cmds:
               cmds[cmd](stuff)
           else:
               print("unknown command '%s'!" %(cmd), file=sys.stderr)
               self.help_cmd()
               sys.exit(1)
        else:
            # Assume we want an interactive console if called without a command
            self.console_interactive()

if __name__ == '__main__':
    app = Application()
    app.main()

