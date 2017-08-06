#!/usr/bin/env python3

"""
Copyright (c) 2015 - present Marco Hinz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import sys
import os
import stat
import time
import textwrap
import argparse
import subprocess
import psutil
import tempfile

from neovim import attach


class Neovim():
    def __init__(self, address, silent=False):
        self.address    = address
        self.server     = None
        self.silent     = silent  # -s
        self._msg_shown = False

    def attach(self):
        try:
            if ':' in self.address:
                ip, port = self.address.split(':')
                self.server = attach('tcp', address=ip, port=int(port))
            else:
                self.server = attach('socket', path=self.address)
        except OSError:
            # Ignore invalid addresses.
            pass

    def is_attached(self, silent=False):
        silent |= self.silent

        if self.server:
            return True
        else:
            address = self.address
            if not ':' in address:
                if os.path.exists(address) and not stat.S_ISSOCK(os.stat(address).st_mode):
                    with tempfile.NamedTemporaryFile(dir='/tmp', prefix='nvimsocket_') as f:
                        self.address = f.name

            if not silent and not self._msg_shown:
                self._show_msg(address)
                self._msg_shown = True

            pid = os.fork()
            if pid == 0:
                for i in range(10):
                    self.attach()
                    if self.server:
                        return True
                    time.sleep(0.2)
            else:
                os.environ['NVIM_LISTEN_ADDRESS'] = self.address
                try:
                    args = os.environ.get('NVR_CMD')
                    args = args.split(' ') if args else ['nvim']
                    os.dup2(sys.stdout.fileno(), sys.stdin.fileno())
                    os.execvpe(args[0], args, os.environ)
                except FileNotFoundError:
                    print("[!] Can't start new nvim process: '{}' is not in $PATH.".format(args[0]))
                    sys.exit(1)

            return False

    def read_stdin_into_buffer(self, cmd):
        self.server.command(cmd)
        for line in sys.stdin:
            self.server.command("call append('$', '{}')".
                    format(line.rstrip().replace("'", "''")))
        self.server.command('silent 1delete _ | set nomodified')

    def execute(self, arguments, cmd='edit', silent=False, wait=False):
        if not self.is_attached(silent):
            return

        cmds, files = split_cmds_from_files(arguments)

        for fname in files:
            if fname == '-':
                self.read_stdin_into_buffer('enew' if cmd == 'edit' else cmd)
            else:
                self.server.command('{} {}'.format(cmd, prepare_filename(fname)))

            if wait:
                bvars = self.server.current.buffer.vars
                chanid = self.server.channel_id

                self.server.command('augroup nvr')
                self.server.command('autocmd BufDelete <buffer> silent! call rpcnotify({}, "BufDelete")'.format(chanid))
                self.server.command('autocmd VimLeave * if exists("v:exiting") && v:exiting > 0 | silent! call rpcnotify({}, "Exit", v:exiting) | endif'.format(chanid))
                self.server.command('augroup END')

                if 'nvr' in bvars:
                    if chanid not in bvars['nvr']:
                        bvars['nvr'] = [chanid] + bvars['nvr']
                else:
                    bvars['nvr'] = [chanid]

        for cmd in cmds:
            self.server.command(cmd if cmd else '$')

        return len(files)

    def _show_msg(self, old_address):
        o = old_address
        print(textwrap.dedent("""
            [!] Can't connect to: {}

                The server (nvim) and client (nvr) have to use the same address.

                Server:

                    Expose $NVIM_LISTEN_ADDRESS to the environment before
                    starting nvim:

                    $ NVIM_LISTEN_ADDRESS={} nvim

                    Use `:echo v:servername` to verify the address.

                Client:

                    Expose $NVIM_LISTEN_ADDRESS to the environment before
                    using nvr or use its --servername option. If neither
                    is given, nvr assumes \"/tmp/nvimsocket\".

                    $ NVIM_LISTEN_ADDRESS={} nvr file1 file2
                    $ nvr --servername {} file1 file2
                    $ nvr --servername 127.0.0.1:6789 file1 file2

                nvr is now starting a server on its own by running $NVR_CMD or 'nvim'.

                Use -s to suppress this message.

            [*] Starting new nvim process with address {}
            """.format(o, o, o, o, self.address)))


def parse_args(argv):
    form_class = argparse.RawDescriptionHelpFormatter
    usage      = '{} [arguments]'.format(argv[0])
    epilog     = 'Happy hacking!'
    desc       = textwrap.dedent("""
        Remote control Neovim processes.

        If no process is found, a new one will be started.

            $ nvr --remote-send 'iabc<cr><esc>'
            $ nvr --remote-expr 'map([1,2,3], \"v:val + 1\")'

        Any arguments not consumed by options will be fed to --remote:

            $ nvr --remote file1 file2
            $ nvr file1 file2

        All --remote options take optional commands.
        Exception: --remote-expr, --remote-send.

            $ nvr +10 file
            $ nvr +'echomsg "foo" | echomsg "bar"' file
            $ nvr --remote-tab-wait +'set bufhidden=delete' file

        Open files in a new window from a terminal buffer:

            $ nvr -cc split file1 file2

        Use nvr from git to edit commit messages:

            $ git config --global core.editor 'nvr --remote-wait-silent'
    """)

    parser = argparse.ArgumentParser(
            formatter_class = form_class,
            usage           = usage,
            epilog          = epilog,
            description     = desc)

    parser.add_argument('--remote',
            nargs   = '*',
            metavar = '<file>',
            help    = 'Use :edit to open files. If no process is found, throw an error and start a new one.')
    parser.add_argument('--remote-wait',
            nargs   = '*',
            metavar = '<file>',
            help    = 'Like --remote, but block until all buffers opened by this option get deleted or the process exits.')
    parser.add_argument('--remote-silent',
            nargs   = '*',
            metavar = '<file>',
            help    = 'Like --remote, but throw no error if no process is found.')
    parser.add_argument('--remote-wait-silent',
            nargs   = '*',
            metavar = '<file>',
            help    = 'Combines --remote-wait and --remote-silent.')

    parser.add_argument('--remote-tab',
            nargs   = '*',
            metavar = '<file>',
            help    = 'Like --remote, but use :tabedit.')
    parser.add_argument('--remote-tab-wait',
            nargs   = '*',
            metavar = '<file>',
            help    = 'Like --remote-wait, but use :tabedit.')
    parser.add_argument('--remote-tab-silent',
            nargs   = '*',
            metavar = '<file>',
            help    = 'Like --remote-silent, but use :tabedit.')
    parser.add_argument('--remote-tab-wait-silent',
            nargs   = '*',
            metavar = '<file>',
            help    = 'Like --remote-wait-silent, but use :tabedit.')

    parser.add_argument('--remote-send',
            metavar = '<keys>',
            help    = 'Send key presses.')
    parser.add_argument('--remote-expr',
            metavar = '<expr>',
            help    = 'Evaluate expression and print result in shell.')

    parser.add_argument('--servername',
            metavar = '<addr>',
            help    = 'Set the address to be used. This overrides the default "/tmp/nvimsocket" and $NVIM_LISTEN_ADDRESS.')
    parser.add_argument('--serverlist',
            action  = 'store_true',
            help    = 'Print the TCPv4 and Unix domain socket addresses of all nvim processes.')

    parser.add_argument('-cc',
            action  = 'append',
            metavar = '<cmd>',
            help    = 'Execute a command before every other option.')
    parser.add_argument('-c',
            action  = 'append',
            metavar = '<cmd>',
            help    = 'Execute a command after every other option.')
    parser.add_argument('-l',
            action  = 'store_true',
            help    = 'Change to previous window via ":wincmd p".')
    parser.add_argument('-o',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Open files via ":split".')
    parser.add_argument('-O',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Open files via ":vsplit".')
    parser.add_argument('-p',
            nargs   = '*',
            metavar = '<file>',
            help    = 'Open files via ":tabedit".')
    parser.add_argument('-q',
            metavar = '<errorfile>',
            help    = 'Read errorfile into quickfix list and display first error.')
    parser.add_argument('-s',
            action  = 'store_true',
            help    = 'Silence "no server found" message.')
    parser.add_argument('-t',
            metavar = '<tag>',
            help    = 'Jump to file and position of given tag.')

    if len(argv) == 1:
        parser.print_help()
        sys.exit(0)

    return parser.parse_known_args(argv[1:])


def split_cmds_from_files(args):
    for i, arg in enumerate(args):
        if arg[0] != '+':
            return [x[1:] for x in reversed(args[:i])], list(reversed(args[i:]))
    return [], []


def prepare_filename(fname):
    return os.path.abspath(fname).replace(" ", "\ ")


def print_sockaddrs():
    sockaddrs = []

    for proc in psutil.process_iter():
        if proc.name() == 'nvim':
            for conn in proc.connections('inet4'):
                sockaddrs.insert(0, ':'.join(map(str, conn.laddr)))
            for conn in proc.connections('unix'):
                if conn.laddr:
                    sockaddrs.insert(0, conn.laddr)

    for addr in sorted(sockaddrs):
        print(addr)


def main(argv=sys.argv, env=os.environ):
    options, arguments = parse_args(argv)
    address = env.get('NVIM_LISTEN_ADDRESS')

    if options.servername:
        address = options.servername
    elif not address:
        address = '/tmp/nvimsocket'

    if options.serverlist:
        print_sockaddrs()

    neovim = Neovim(address, options.s)
    neovim.attach()

    if options.cc and neovim.is_attached():
        for cmd in options.cc:
            neovim.server.command(cmd)

    if options.l and neovim.is_attached():
        neovim.server.command('wincmd p')

    try:
        arguments.remove('--')
    except ValueError:
        pass

    if options.remote is not None:
        neovim.execute(options.remote + arguments, 'edit')
    elif options.remote_wait is not None:
        nfiles = neovim.execute(options.remote_wait + arguments, 'edit', wait=True)
    elif options.remote_silent is not None:
        neovim.execute(options.remote_silent + arguments, 'edit', silent=True)
    elif options.remote_wait_silent is not None:
        nfiles = neovim.execute(options.remote_wait_silent + arguments, 'edit', silent=True, wait=True)
    elif options.remote_tab is not None:
        neovim.execute(options.remote_tab + arguments, 'tabedit')
    elif options.remote_tab_wait is not None:
        nfiles = neovim.execute(options.remote_tab_wait + arguments, 'tabedit', wait=True)
    elif options.remote_tab_silent is not None:
        neovim.execute(options.remote_tab_silent + arguments, 'tabedit', silent=True)
    elif options.remote_tab_wait_silent is not None:
        nfiles = neovim.execute(options.remote_tab_wait_silent + arguments, 'tabedit', silent=True, wait=True)
    elif arguments:
        neovim.execute(arguments, 'edit')

    if options.remote_send and neovim.is_attached():
        neovim.server.input(options.remote_send)

    if options.remote_expr and neovim.is_attached():
        result = ''
        try:
            result = neovim.server.eval(options.remote_expr)
        except:
            print('Evaluation failed: ' + options.remote_expr)
        if type(result) is bytes:
            print(result.decode())
        elif type(result) is list:
            print(list(map(lambda x: x.decode() if type(x) is bytes else x, result)))
        elif type(result) is dict:
            print({ (k.decode() if type(k) is bytes else k): v for (k,v) in result.items() })
        else:
            print(result)

    if options.o and neovim.is_attached():
        for fname in options.o:
            if fname == '-':
                neovim.read_stdin_into_buffer('new')
            else:
                neovim.server.command('split {}'.format(prepare_filename(fname)))
    if options.O and neovim.is_attached():
        for fname in options.O:
            if fname == '-':
                neovim.read_stdin_into_buffer('vnew')
            else:
                neovim.server.command('vsplit {}'.format(prepare_filename(fname)))

    if options.t and neovim.is_attached():
        try:
            neovim.server.command("tag {}".format(options.t))
        except neovim.server.error as e:
            print(e)
            sys.exit(1)

    if options.q and neovim.is_attached():
        neovim.server.command("silent execute 'lcd' fnameescape('{}')".
                format(os.environ['PWD'].replace("'", "''")))
        neovim.server.command('call setqflist([])')
        with open(options.q, 'r') as f:
            for line in f.readlines():
                neovim.server.command("caddexpr '{}'".
                        format(line.rstrip().replace("'", "''").replace('|', '\|')))
        neovim.server.command('silent lcd -')
        neovim.server.command('cfirst')

    if options.c and neovim.is_attached():
        for cmd in options.c:
            neovim.server.command(cmd)

    if 'nfiles' in locals():
        exitcode = 0

        def notification_cb(msg, args):
            nonlocal nfiles
            nonlocal exitcode

            if msg == 'BufDelete':
                nfiles -= 1
                if nfiles == 0:
                    neovim.server.stop_loop()
            elif msg == 'Exit':
                neovim.server.stop_loop()
                exitcode = args[0]

        def err_cb(error):
            print(error, file=sys.stderr)
            neovim.server.stop_loop()
            exitcode = 1

        neovim.server.run_loop(None, notification_cb, None, err_cb)
        sys.exit(exitcode)


if __name__ == '__main__':
    main()

