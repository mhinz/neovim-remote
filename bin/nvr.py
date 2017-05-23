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
import textwrap
import argparse
import subprocess
import psutil

from neovim import attach


class Neovim():
    def __init__(self, address):
        self.address    = address
        self.server     = None
        self._msg_shown = False

    def attach(self):
        try:
            if ':' in self.address:
                ip, port = self.address.split(':')
                self.server = attach('tcp', address=ip, port=int(port))
            else:
                self.server = attach('socket', path=self.address)
        except:
            pass

    def is_attached(self, silent=False):
        if self.server:
            return True
        else:
            if not silent and not self._msg_shown:
                self._show_msg()
                self._msg_shown = True
            return False

    def read_stdin_into_buffer(self, cmd):
        self.server.command(cmd)
        for line in sys.stdin:
            self.server.command("call append('$', '{}')".
                    format(line.rstrip().replace("'", "''")))
        self.server.command('silent 1delete _ | set nomodified')

    def execute(self, arguments, cmd='edit', silent=False, wait=False):
        if self.is_attached(silent):
            self._execute_remotely(arguments, cmd, wait)
        else:
            self._execute_locally(arguments, silent)

    def _execute_locally(self, arguments, silent):
        if not arguments and not silent:
            print('No arguments were given!')
        else:
            env = os.environ.copy()
            env['NVIM_LISTEN_ADDRESS'] = self.address
            subprocess.Popen(['nvim'] + arguments, env=env).wait()

    def _execute_remotely(self, arguments, cmd, wait):
        c = None
        for fname in reversed(arguments):
            if fname.startswith('+'):
                c = fname[1:]
                continue

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

        if c:
            self.server.command(c)

        if wait:
            bufcount = len(arguments) - (1 if c else 0)
            exitcode = 0

            def notification_cb(msg, args):
                nonlocal bufcount
                nonlocal exitcode

                if msg == 'BufDelete':
                    bufcount -= 1
                    if bufcount == 0:
                        self.server.stop_loop()
                elif msg == 'Exit':
                    self.server.stop_loop()
                    exitcode = args[0]

            def err_cb(error):
                print(error, file=sys.stderr)
                self.server.stop_loop()
                exitcode = 1

            self.server.run_loop(None, notification_cb, None, err_cb)
            sys.exit(exitcode)

    def _show_msg(self):
        a = self.address
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

                Use any of the --remote*silent options to suppress this message.

            [*] Starting new nvim instance with address: {}
            """.format(a, a, a, a, a)))


def parse_args():
    form_class = argparse.RawDescriptionHelpFormatter
    usage      = '{} [arguments]'.format(sys.argv[0])
    epilog     = 'Happy hacking!'
    desc       = textwrap.dedent("""
        Remote control Neovim instances.

            $ nvr --remote-send 'iabc<cr><esc>'
            $ nvr --remote-expr 'map([1,2,3], \"v:val + 1\")'

        Any arguments not consumed by options will be fed to --remote. If no remote
        instance is found, a new one will be started.

            $ nvr --remote file1 file2
            $ nvr file1 file2

        All --remote flags take optional commands. Except: --remote-expr, --remote-send.

            $ nvr +10 file
            $ nvr +'echomsg "foo" | echomsg "bar"' file
            $ nvr --remote-tab-wait +'set bufhidden=delete' file

        Open files in a new window from within :terminal

            $ nvr -cc split file1 file2

    """)

    parser = argparse.ArgumentParser(
            formatter_class = form_class,
            usage           = usage,
            epilog          = epilog,
            description     = desc)

    parser.add_argument('--remote',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Use :edit to open files in a remote instance. If no remote instance is found, throw an error and run nvim locally instead.')
    parser.add_argument('--remote-wait',
            nargs   = '*',
            metavar = '<file>',
            help    = 'Like --remote, but block until all buffers opened by this option get deleted or remote instance exits.')
    parser.add_argument('--remote-silent',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Like --remote, but throw no error if remote instance is not found.')
    parser.add_argument('--remote-wait-silent',
            nargs   = '*',
            metavar = '<file>',
            help    = 'Combines --remote-wait and --remote-silent.')

    parser.add_argument('--remote-tab', '-p',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Like --remote, but use :tabedit.')
    parser.add_argument('--remote-tab-wait',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Like --remote-wait, but use :tabedit.')
    parser.add_argument('--remote-tab-silent',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Like --remote-silent, but use :tabedit.')
    parser.add_argument('--remote-tab-wait-silent',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Like --remote-wait-silent, but use :tabedit.')

    parser.add_argument('--remote-send',
            metavar = '<keys>',
            help    = 'Send key presses.')
    parser.add_argument('--remote-expr',
            metavar = '<expr>',
            help    = 'Evaluate expression on remote instance and print result in shell.')

    parser.add_argument('--servername',
            metavar = '<addr>',
            help    = 'Set the address to be used. This overrides the default "/tmp/nvimsocket" and $NVIM_LISTEN_ADDRESS.')
    parser.add_argument('--serverlist',
            action  = 'store_true',
            help    = 'Print the TCPv4 and Unix domain socket addresses of all nvim processes.')

    parser.add_argument('-l',
            action  = 'store_true',
            help    = 'Change to previous window via ":wincmd p".')
    parser.add_argument('-cc',
            action  = 'append',
            metavar = '<cmd>',
            help    = 'Execute a command before every other option.')
    parser.add_argument('-c',
            action  = 'append',
            metavar = '<cmd>',
            help    = 'Execute a command after every other option.')
    parser.add_argument('-o',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Open files via ":split".')
    parser.add_argument('-O',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Open files via ":vsplit".')
    parser.add_argument('-t',
            metavar = '<tag>',
            help    = 'Jump to file and position of given tag.')
    parser.add_argument('-q',
            metavar = '<errorfile>',
            help    = 'Read errorfile into quickfix list and display first error.')


    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    return parser.parse_known_args()


def prepare_filename(fname):
    return os.path.abspath(fname).replace(" ", "\ ")


def print_sockaddrs():
    sockaddrs = []

    for proc in psutil.process_iter():
        if proc.name() == 'nvim':
            for conn in proc.connections('inet4'):
                sockaddrs.insert(0, ':'.join(map(str, conn.laddr)))
            for conn in proc.connections('unix'):
                sockaddrs.insert(0, conn.laddr)

    for addr in sorted(sockaddrs):
        print(addr)


def main():
    flags, arguments = parse_args()
    address = os.environ.get('NVIM_LISTEN_ADDRESS')

    if flags.servername:
        address = flags.servername
    elif not address:
        address = '/tmp/nvimsocket'

    if flags.serverlist:
        print_sockaddrs()

    neovim = Neovim(address)
    neovim.attach()

    if flags.cc and neovim.is_attached():
        for cmd in flags.cc:
            neovim.server.command(cmd)

    if flags.l and neovim.is_attached():
        neovim.server.command('wincmd p')

    try:
        arguments.remove('--')
    except ValueError:
        pass

    # Arguments not consumed by flags, are fed to --remote.
    if arguments:
        neovim.execute(arguments, 'edit')
    elif flags.remote:
        neovim.execute(flags.remote, 'edit')
    elif flags.remote_wait:
        neovim.execute(flags.remote_wait, 'edit', wait=True)
    elif flags.remote_silent:
        neovim.execute(flags.remote_silent, 'edit', silent=True)
    elif flags.remote_wait_silent:
        neovim.execute(flags.remote_wait_silent, 'edit', silent=True, wait=True)
    elif flags.remote_tab:
        neovim.execute(flags.remote_tab, 'tabedit')
    elif flags.remote_tab_wait:
        neovim.execute(flags.remote_tab_wait, 'tabedit', wait=True)
    elif flags.remote_tab_silent:
        neovim.execute(flags.remote_tab_silent, 'tabedit', silent=True)
    elif flags.remote_tab_wait_silent:
        neovim.execute(flags.remote_tab_wait_silent, 'tabedit', silent=True, wait=True)

    if flags.remote_send and neovim.is_attached():
        neovim.server.input(flags.remote_send)

    if flags.remote_expr and neovim.is_attached():
        result = ''
        try:
            result = neovim.server.eval(flags.remote_expr)
        except:
            print('Evaluation failed: ' + flags.remote_expr)
        if type(result) is bytes:
            print(result.decode())
        elif type(result) is list:
            print(list(map(lambda x: x.decode() if type(x) is bytes else x, result)))
        elif type(result) is dict:
            print({ (k.decode() if type(k) is bytes else k): v for (k,v) in result.items() })
        else:
            print(result)

    if flags.o and neovim.is_attached():
        for fname in flags.o:
            if fname == '-':
                neovim.read_stdin_into_buffer('new')
            else:
                neovim.server.command('split {}'.format(prepare_filename(fname)))
    if flags.O and neovim.is_attached():
        for fname in flags.O:
            if fname == '-':
                neovim.read_stdin_into_buffer('vnew')
            else:
                neovim.server.command('vsplit {}'.format(prepare_filename(fname)))

    if flags.t and neovim.is_attached():
        try:
            neovim.server.command("tag {}".format(flags.t))
        except neovim.server.error as e:
            print(e)
            sys.exit(1)

    if flags.q and neovim.is_attached():
        neovim.server.command("silent execute 'lcd' fnameescape('{}')".
                format(os.environ['PWD'].replace("'", "''")))
        neovim.server.command('call setqflist([])')
        with open(flags.q, 'r') as f:
            for line in f.readlines():
                neovim.server.command("caddexpr '{}'".
                        format(line.rstrip().replace("'", "''").replace('|', '\|')))
        neovim.server.command('silent lcd -')
        neovim.server.command('cfirst')

    if flags.c and neovim.is_attached():
        for cmd in flags.c:
            neovim.server.command(cmd)


if __name__ == '__main__':
    main()

