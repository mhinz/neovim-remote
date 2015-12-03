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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote', action='append', help='Edit <files> in a Vim server if possible')
    parser.add_argument('--remote-silent',      help="Same, don't complain if there is no server")
    parser.add_argument('--remote-wait', action='append', help='As --remote but wait for files to have been edited')
    parser.add_argument('--remote-wait-silent', help="Same, don't complain if there is no server")
    parser.add_argument('--remote-tab', action='append', help='As --remote but use tab page per file')
    parser.add_argument('--remote-send', action='append', help='Send <keys> to a Vim server and exit')
    parser.add_argument('--remote-expr', action='append', help='Evaluate <expr> in a Vim server and print result')
    args, unused = parser.parse_known_args()

    sockpath = os.environ.get('NVIM_LISTEN_ADDRESS')
    if sockpath is None:
        sockpath = '/tmp/nvimsocket'

    try:
        nvim = attach('socket', path='/tmp/nvimsocket')
    except FileNotFoundError:
        print("""Problem:  Can't find unix socket: /tmp/nvimsocket
    Solution: Start a new server:  NVIM_LISTEN_ADDRESS=/tmp/nvimsocket nvim""")
        sys.exit(1)

    if args.remote:
        for fname in args.remote:
            nvim.command('edit {}'.format(fname))

    # Not implemented yet.
    if args.remote_silent:
        pass

    # Hint: Same as --remote.
    if args.remote_wait:
        for fname in args.remote_wait:
            nvim.command('edit {}'.format(fname))

    # Not implemented yet.
    if args.remote_wait_silent:
        pass

    if args.remote_tab:
        for fname in args.remote_tab:
            nvim.command('tabedit {}'.format(fname))

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
