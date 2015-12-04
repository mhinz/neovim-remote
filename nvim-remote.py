#!/usr/bin/env python3

"""
Copyright (c) 2015 Marco Hinz

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
import subprocess
import argparse

from neovim import attach

class Neovim():
    """Thin wrapper around nvim.attach() for lazy attaching.

    This helps handling the silent and non-silent arguments.
    """
    def __init__(self, sockpath):
        self.sockpath = sockpath
        self.server = None

    def attached(self, silent=False):
        if self.server is not None:
            return True
        try:
            self.server = attach('socket', path=self.sockpath)
            return True
        except FileNotFoundError:
            if silent:
                return False
            else:
                print("Can't find unix socket {}. Set NVIM_LISTEN_ADDRESS.".format(self.sockpath))
                sys.exit(1)


def parse_args():
    usage  = '{} [arguments]'.format(sys.argv[0])
    desc   = 'nvim wrapper that provides --remote and friends.'
    epilog = 'Happy hacking!'
    parser = argparse.ArgumentParser(usage=usage, description=desc, epilog=epilog)

    parser.add_argument('--remote',
        action='append',
        metavar='<file>',
        help='open file in new buffer [ASYNC]')
    parser.add_argument('--remote-wait',
        action='append',
        metavar='<file>',
        help='as --remote [SYNC]')
    parser.add_argument('--remote-silent',
        action='append',
        metavar='<file>',
        help="as --remote, but don't throw error if no server is found [ASYNC]")
    parser.add_argument('--remote-wait-silent',
        action='append',
        metavar='<file>',
        help="as --remote, but don't throw error if no server is found [SYNC]")
    parser.add_argument('--remote-tab',
        action='append',
        metavar='<file>',
        help='open file in new tab [SYNC]')
    parser.add_argument('--remote-send',
        action='append',
        metavar='<keys>',
        help='send keys to server [SYNC]')
    parser.add_argument('--remote-expr',
        action='append',
        metavar='<expr>',
        help='evaluate expression and print result [SYNC]')

    return parser.parse_known_args()


def main():
    args, unused = parse_args()

    sockpath = os.environ.get('NVIM_LISTEN_ADDRESS')
    if sockpath is None:
        sockpath = '/tmp/nvimsocket'

    n = Neovim(sockpath)

    if args.remote_silent and n.attached(silent=True):
        for fname in args.remote_silent:
            n.server.command('edit {}'.format(fname.replace(" ", "\ ")), async=True)
    if args.remote_wait_silent and n.attached(silent=True):
        for fname in args.remote_wait_silent:
            n.server.command('edit {}'.format(fname.replace(" ", "\ ")))
    if args.remote and n.attached():
        for fname in args.remote:
            n.server.command('edit {}'.format(fname.replace(" ", "\ ")), async=True)
    if args.remote_wait and n.attached():
        for fname in args.remote_wait:
            n.server.command('edit {}'.format(fname.replace(" ", "\ ")))
    if args.remote_tab and n.attached():
        for fname in args.remote_tab:
            n.server.command('tabedit {}'.format(fname.replace(" ", "\ ")))
    if args.remote_send and n.attached():
        for keys in args.remote_send:
            n.server.input(keys)
    if args.remote_expr and n.attached():
        for expr in args.remote_expr:
            print(n.server.eval(expr))

    # If none of the wrapper arguments were given, fall back to normal nvim usage.
    if all(x is None for x in vars(args).values()):
        try:
            # Run interactive shell in case 'nvim' is an alias.
            subprocess.run([os.environ.get('SHELL'), '-ic', 'nvim ' + ' '.join(unused)])
        except FileNotFoundError:
            print("Not in $PATH: nvim")
            sys.exit(1)

if __name__ == '__main__':
    main()
