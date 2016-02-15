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

from neovim import attach


class Neovim():
    """Thin wrapper around nvim.attach() for lazy attaching.

    This helps handling the silent and non-silent arguments.
    """
    def __init__(self, addr):
        self.addr   = addr
        self.server = None

    def attached(self, silent=False):
        if self.server is not None:
            return True
        try:
            addr = self.addr.split(':')
            if len(addr) == 1:
                self.server = attach('socket', path=self.addr)
            else:
                ip, port = addr
                self.server = attach("tcp", address=ip, port=int(port))
            return True
        except:
            if silent:
                return False
            else:
                print("Can't connect to {}. Export $NVIM_LISTEN_ADDRESS or use --servername".format(self.addr))
                sys.exit(1)


def parse_args():
    form_class = argparse.RawDescriptionHelpFormatter
    usage      = '{} [arguments]'.format(sys.argv[0])
    epilog     = 'Happy hacking!'
    desc       = textwrap.dedent("""
        Helper tool for nvim that provides --remote and friends.

        All unused arguments will be implicitely fed to --remote-silent.
        Thus the following two lines are equivalent:

            $ nvr --remote-silent foo bar quux
            $ nvr foo bar quux
    """)

    parser = argparse.ArgumentParser(
            formatter_class = form_class,
            usage           = usage,
            epilog          = epilog,
            description     = desc)

    # The following options are similar to their vim equivalents,
    # but work on the remote instance instead.

    parser.add_argument('-l',
            action  = 'store_true',
            help    = 'Change to previous window via ":wincmd p".')
    parser.add_argument('-c',
            action  = 'append',
            metavar = '<cmd>',
            help    = 'Execute single command.')
    parser.add_argument('-o',
            action  = 'store',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Open files via ":split".')
    parser.add_argument('-O',
            action  = 'store',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Open files via ":vsplit".')

    # The following options exactly emulate their vim equivalents.

    parser.add_argument('--remote',
            action  = 'store',
            nargs   = '+',
            metavar = '<file>',
            help    = 'Open files via ":edit". If the first argument is "+cmd", "cmd" will be executed for the first file. E.g. "--remote +10 file1 file2" will first open file2, then file1, then execute :10.')
    parser.add_argument('--remote-wait',
            action  = 'store',
            nargs   = '+',
            metavar = '<file>',
            help    = 'As --remote.')
    parser.add_argument('--remote-silent',
            action  = 'store',
            nargs   = '+',
            metavar = '<file>',
            help    = "As --remote, but don't throw error if no server is found.")
    parser.add_argument('--remote-wait-silent',
            action  = 'store',
            nargs   = '+',
            metavar = '<file>',
            help    = "As --remote, but don't throw error if no server is found.")
    parser.add_argument('--remote-tab', '-p',
            action  = 'store',
            nargs   = '+',
            metavar = '<file>',
            help    = 'As --remote, but uses :tabedit.')
    parser.add_argument('--remote-tab-wait',
            action  = 'store',
            nargs   = '+',
            metavar = '<file>',
            help    = 'As --remote-tab.')
    parser.add_argument('--remote-tab-silent',
            action  = 'store',
            nargs   = '+',
            metavar = '<file>',
            help    = "As --remote-tab, but don't throw error if no server is found.")
    parser.add_argument('--remote-tab-wait-silent',
            action  = 'store',
            nargs   = '+',
            metavar = '<file>',
            help    = "As --remote-tab, but don't throw error if no server is found.")
    parser.add_argument('--remote-send',
            action  = 'store',
            nargs   = '+',
            metavar = '<keys>',
            help    = "Send key presses. E.g. \"-l --remote-send 'iabc<cr><esc>'\".")
    parser.add_argument('--remote-expr',
            action  = 'store',
            nargs   = '+',
            metavar = '<expr>',
            help    = "Evaluate expression on server and print result in shell. E.g. \"--remote-expr 'v:progpath'\".")
    parser.add_argument('--servername',
            metavar = '<addr>',
            help    = 'Set the address to be used (overrides $NVIM_LISTEN_ADDRESS).')
    parser.add_argument('--serverlist',
            action  = 'store_true',
            help    = 'Print the used address (TCP, Unix domain, or named pipe).')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    return parser.parse_known_args()

def prepare_filename(fname):
    return os.path.abspath(fname).replace(" ", "\ ")

def open(n, filenames, cmd, async=False):
    c = None
    if filenames[0][0] == '+':
        c = filenames[0][1:]
        filenames = filenames[1:]
    for fname in reversed(filenames):
        n.server.command('{} {}'.format(cmd, prepare_filename(fname)), async=async)
    if c:
        n.server.command(c)

def run():
    args, unused = parse_args()
    addr = os.environ.get('NVIM_LISTEN_ADDRESS')

    if args.servername:
        addr = args.servername
    else:
        if not addr:
            addr = '/tmp/nvimsocket'

    if args.serverlist:
        if addr:
            print(addr)

    n = Neovim(addr)

    if args.l and n.attached(silent=True):
        n.server.command('wincmd p', async=True)

    if unused and n.attached(silent=True):
        open(n, unused, 'edit', async=True)

    if args.remote_silent and n.attached(silent=True):
        open(n, args.remote_silent, 'edit', async=True)
    if args.remote_wait_silent and n.attached(silent=True):
        open(n, args.remote_wait_silent, 'edit')
    if args.remote_tab_silent and n.attached():
        open(n, args.remote_tab_silent, 'tabedit', async=True)
    if args.remote_tab_wait_silent and n.attached():
        open(n, args.remote_tab_wait_silent, 'tabedit')

    if args.remote and n.attached():
        open(n, args.remote, 'edit', async=True)
    if args.remote_wait and n.attached():
        open(n, args.remote_wait, 'edit')
    if args.remote_tab and n.attached():
        open(n, args.remote_tab, 'tabedit', async=True)
    if args.remote_tab_wait and n.attached():
        open(n, args.remote_tab_wait, 'tabedit')

    if args.remote_send and n.attached():
        for keys in args.remote_send:
            n.server.input(keys)

    if args.remote_expr and n.attached():
        for expr in args.remote_expr:
            result = ''
            try:
                result = n.server.eval(expr)
            except:
                print('Evaluation failed: ' + expr)
                continue
            if type(result) is bytes:
                print(result.decode())
            elif type(result) is list:
                print(list(map(lambda x: x.decode() if type(x) is bytes else x, result)))
            elif type(result) is dict:
                print({ (k.decode() if type(k) is bytes else k): v for (k,v) in result.items() })
            else:
                print(result)

    if args.o and n.attached():
        for fname in args.o:
            n.server.command('split {}'.format(prepare_filename(fname)), async=True)

    if args.O and n.attached():
        for fname in args.O:
            n.server.command('vsplit {}'.format(prepare_filename(fname)), async=True)

    if args.c and n.attached():
        for cmd in args.c:
            n.server.command(cmd)
