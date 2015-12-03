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
import platform
import argparse

from neovim import attach

def parse_args():
    usage  = '{} [arguments]'.format(sys.argv[0])
    desc   = 'nvim wrapper that provides --remote and friends.'
    epilog = 'Happy hacking!'
    parser = argparse.ArgumentParser(usage=usage, description=desc, epilog=epilog)

    parser.add_argument('--remote',
        action='append',
        metavar='<file>',
        help='Edit <files> in a Neovim server.')
    parser.add_argument('--remote-silent',
        action='append',
        metavar='<file>',
        help='[Not implemented yet]')
    parser.add_argument('--remote-wait',
        action='append',
        metavar='<file>',
        help='Same as --remote.')
    parser.add_argument('--remote-wait-silent',
        action='append',
        metavar='<file>',
        help='[Not implemented yet]')
    parser.add_argument('--remote-tab',
        action='append',
        metavar='<file>',
        help='As --remote, but uses one tab page per file.')
    parser.add_argument('--remote-send',
        action='append',
        metavar='<keys>',
        help='Send <keys> to Neovim server.')
    parser.add_argument('--remote-expr',
        action='append',
        metavar='<expr>',
        help='Evaluate <expr> in Neovim server and print result.')
    parser.add_argument('--terminal',
        metavar='<termemu>',
        help='Use the given terminal emulator to start a new server.')

    return parser.parse_known_args()

def main():
    args, unused = parse_args()

    sockpath = os.environ.get('NVIM_LISTEN_ADDRESS')
    if sockpath is None:
        sockpath = '/tmp/nvimsocket'

    try:
        nvim = attach('socket', path=sockpath)
    except FileNotFoundError:
        print("Can't find unix socket {}. Set NVIM_LISTEN_ADDRESS.".format(sockpath))
        sys.exit(1)

    if args.remote:
        for fname in args.remote:
            nvim.command('edit {}'.format(fname.replace(" ", "\ ")))

    if args.remote_silent:
        pass

    if args.remote_wait:
        for fname in args.remote_wait:
            nvim.command('edit {}'.format(fname.replace(" ", "\ ")))

    if args.remote_wait_silent:
        pass

    if args.remote_tab:
        for fname in args.remote_tab:
            nvim.command('tabedit {}'.format(fname.replace(" ", "\ ")))

    if args.remote_send:
        for keys in args.remote_send:
            nvim.input(keys)

    if args.remote_expr:
        for expr in args.remote_expr:
            print(nvim.eval(expr))

    if unused:
        os.putenv('VIMRUNTIME', '/data/repo/neovim/runtime')
        subprocess.Popen(['/data/repo/neovim/build/bin/nvim'] + unused)

if __name__ == '__main__':
    main()
