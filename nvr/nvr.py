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

import argparse
import pynvim
import os
import psutil
import re
import socket
import sys
import textwrap
import time
import traceback
import uuid


class Nvr():
    def __init__(self, address, silent=False):
        self.address = address
        self.server = None
        self.silent = silent
        self.wait = 0
        self.started_new_process = False
        self.handled_first_buffer = False
        self.diffmode = False
        self._msg_shown = False

    def attach(self):
        try:
            if get_address_type(self.address) == 'tcp':
                ip, port = self.address.split(':', 1)
                self.server = pynvim.attach('tcp', address=ip, port=int(port))
            else:
                self.server = pynvim.attach('socket', path=self.address)
        except OSError:
            # Ignore invalid addresses.
            pass

    def start_new_process(self):
        args = os.environ.get('NVR_CMD')
        args = args.split(' ') if args else ['nvim']
        pid = os.fork()
        if pid == 0:
            for i in range(10):
                self.attach()
                if self.server:
                    self.started_new_process = True
                    return True
                time.sleep(0.2)
            print('[!] Unable to attach to the new nvim process. Is `{}` working?'
                    .format(" ".join(args)))
            sys.exit(1)
        else:
            os.environ['NVIM_LISTEN_ADDRESS'] = self.address
            try:
                os.dup2(sys.stdout.fileno(), sys.stdin.fileno())
                os.execvpe(args[0], args, os.environ)
            except FileNotFoundError:
                print("[!] Can't start new nvim process: '{}' is not in $PATH.".format(args[0]))
                sys.exit(1)

    def read_stdin_into_buffer(self, cmd):
        self.server.command(cmd)
        for line in sys.stdin:
            self.server.funcs.append('$', line.rstrip())
        self.server.command('silent 1delete _ | set nomodified')

    def fnameescaped_command(self, cmd, path):
        if not is_netrw_protocol(path):
            path = os.path.abspath(path)
        path = self.server.funcs.fnameescape(path)
        shortmess = self.server.options['shortmess']
        self.server.options['shortmess'] = shortmess.replace('F', '')
        self.server.command('{} {}'.format(cmd, path))
        self.server.options['shortmess'] = shortmess

    def diffthis(self):
        if self.diffmode:
            self.server.command('diffthis')
            if not self.started_new_process:
                self.wait_for_current_buffer()

    def wait_for_current_buffer(self):
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

        self.wait += 1

    def execute(self, arguments, cmd='edit', silent=False, wait=False):
        cmds, files = split_cmds_from_files(arguments)

        for fname in files:
            if fname == '-':
                self.read_stdin_into_buffer('enew' if cmd == 'edit' else cmd)
            else:
                try:
                    if self.started_new_process and not self.handled_first_buffer:
                        self.fnameescaped_command('edit', fname)
                        self.handled_first_buffer = True
                    else:
                        self.fnameescaped_command(cmd, fname)
                except pynvim.api.nvim.NvimError as e:
                    if not re.search('E37', e.args[0].decode()):
                        traceback.print_exc()
                        sys.exit(1)

            if wait:
                self.wait_for_current_buffer()

        for cmd in cmds:
            self.server.command(cmd if cmd else '$')

        return len(files)


def is_netrw_protocol(path):
    protocols = [
            re.compile('^davs?://*'),
            re.compile('^file://*'),
            re.compile('^ftp://*'),
            re.compile('^https?://*'),
            re.compile('^rcp://*'),
            re.compile('^rsync://*'),
            re.compile('^scp://*'),
            re.compile('^sftp://*'),
            ]

    return True if any(prot.match(path) for prot in protocols) else False


def sanitize_address(address):
    if get_address_type(address) == 'socket' and os.path.exists(address):
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(address)
        except:
            address = '/tmp/nvimsocket-{}'.format(uuid.uuid4())

    return address


def parse_args(argv):
    form_class = argparse.RawDescriptionHelpFormatter
    usage      = '{} [arguments]'.format(argv[0])
    epilog     = 'Development: https://github.com/mhinz/neovim-remote\n\nHappy hacking!'
    desc       = textwrap.dedent("""
        Remote control Neovim processes.

        If no process is found, a new one will be started.

            $ nvr --remote-send 'iabc<cr><esc>'
            $ nvr --remote-expr 'map([1,2,3], \"v:val + 1\")'

        Any arguments not consumed by options will be fed to --remote-silent:

            $ nvr --remote-silent file1 file2
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
    parser.add_argument('-d',
            action  = 'store_true',
            help    = 'Diff mode. Use :diffthis on all to be opened buffers.')
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
            nargs   = '+',
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
    parser.add_argument('--nostart',
            action  = 'store_true',
            help    = 'If no process is found, do not start a new one.')
    parser.add_argument('--version',
            action  = 'store_true',
            help    = 'Show the nvr version.')

    return parser.parse_known_args(argv[1:])


def show_message(old_address, new_address):
    print(textwrap.dedent("""
        [!] Can't connect to: {}

            The server (nvim) and client (nvr) have to use the same address.

            Server:

                Expose $NVIM_LISTEN_ADDRESS to the environment before
                starting nvim:

                $ NVIM_LISTEN_ADDRESS={} nvim

                Use `:echo v:servername` to verify the address.

                Security: When using Unix domain sockets on a multi-user system,
                the socket should have proper permissions so that it is only
                accessible by your user.

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
        """.format(old_address, old_address, old_address, old_address, new_address)))


def split_cmds_from_files(args):
    for i, arg in enumerate(args):
        if arg[0] != '+':
            return [x[1:] for x in reversed(args[:i])], list(reversed(args[i:]))
    return [], []


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


def get_address_type(address):
    try:
        ip, port = address.split(':', 1)
        if port.isdigit():
            return 'tcp'
        raise ValueError
    except ValueError:
        return 'socket'


def main(argv=sys.argv, env=os.environ):
    options, arguments = parse_args(argv)

    if options.version:
        import pkg_resources
        version = pkg_resources.require('neovim-remote')[0].version
        print('nvr {}'.format(version))
        return

    if options.serverlist:
        print_sockaddrs()
        return

    address = options.servername or env.get('NVIM_LISTEN_ADDRESS') or '/tmp/nvimsocket'

    nvr = Nvr(address, options.s)
    nvr.attach()

    if not nvr.server:
        nvr.address = sanitize_address(address)
        silent = options.remote_silent or options.remote_wait_silent or options.remote_tab_silent or options.remote_tab_wait_silent or options.s
        if not silent:
            show_message(address, nvr.address)
        if options.nostart:
            sys.exit(1)
        nvr.start_new_process()

    if not nvr.server:
        raise RuntimeError('This should never happen. Please raise an issue at https://github.com/mhinz/neovim-remote/issues')

    if options.d:
        nvr.diffmode = True

    if options.cc:
        for cmd in options.cc:
            if cmd == '-':
                cmd = sys.stdin.read()
            nvr.server.command(cmd)

    if options.l:
        nvr.server.command('wincmd p')

    try:
        arguments.remove('--')
    except ValueError:
        pass

    if options.remote is not None:
        nvr.execute(options.remote + arguments, 'edit')
    elif options.remote_wait is not None:
        nvr.execute(options.remote_wait + arguments, 'edit', wait=True)
    elif options.remote_silent is not None:
        nvr.execute(options.remote_silent + arguments, 'edit', silent=True)
    elif options.remote_wait_silent is not None:
        nvr.execute(options.remote_wait_silent + arguments, 'edit', silent=True, wait=True)
    elif options.remote_tab is not None:
        nvr.execute(options.remote_tab + arguments, 'tabedit')
    elif options.remote_tab_wait is not None:
        nvr.execute(options.remote_tab_wait + arguments, 'tabedit', wait=True)
    elif options.remote_tab_silent is not None:
        nvr.execute(options.remote_tab_silent + arguments, 'tabedit', silent=True)
    elif options.remote_tab_wait_silent is not None:
        nvr.execute(options.remote_tab_wait_silent + arguments, 'tabedit', silent=True, wait=True)
    elif arguments:
        if options.d:
            # Emulate `vim -d`.
            options.O = arguments
        else:
            # Act like --remote-silent by default.
            nvr.execute(arguments, 'edit', silent=True)

    if options.remote_send:
        nvr.server.input(options.remote_send)

    if options.remote_expr:
        result = ''
        if options.remote_expr == '-':
            options.remote_expr = sys.stdin.read()
        try:
            result = nvr.server.eval(options.remote_expr)
        except:
            print(textwrap.dedent("""
                No valid expression: {}
                Test it in Neovim: :echo eval('...')
                If you want to execute a command, use -c or -cc instead.
            """).format(options.remote_expr))
        if type(result) is bytes:
            print(result.decode())
        elif type(result) is list:
            print(list(map(lambda x: x.decode() if type(x) is bytes else x, result)))
        elif type(result) is dict:
            print({ (k.decode() if type(k) is bytes else k): v for (k,v) in result.items() })
        else:
            print(result)

    if options.o:
        if nvr.started_new_process:
            cmd = 'edit'
        elif options.d:
            cmd = 'tabedit'
        else:
            cmd = 'split'
        nvr.fnameescaped_command(cmd, options.o.pop(0))
        nvr.diffthis()
        for fname in options.o:
            if fname == '-':
                nvr.read_stdin_into_buffer('new')
            else:
                nvr.fnameescaped_command('split', fname)
            nvr.diffthis()
        nvr.server.command('wincmd =')

    if options.O:
        if nvr.started_new_process:
            cmd = 'edit'
        elif options.d:
            cmd = 'tabedit'
        else:
            cmd = 'vsplit'
        nvr.fnameescaped_command(cmd, options.O.pop(0))
        nvr.diffthis()
        for fname in options.O:
            if fname == '-':
                nvr.read_stdin_into_buffer('vnew')
            else:
                nvr.fnameescaped_command('vsplit', fname)
            nvr.diffthis()
        nvr.server.command('wincmd =')

    if options.p:
        cmd = 'edit' if nvr.started_new_process else 'tabedit'
        nvr.fnameescaped_command(cmd, options.p.pop(0))
        for fname in options.p:
            if fname == '-':
                nvr.read_stdin_into_buffer('tabnew')
            else:
                nvr.fnameescaped_command('tabedit', fname)

    if options.t:
        try:
            nvr.server.command("tag {}".format(options.t))
        except nvr.server.error as e:
            print(e)
            sys.exit(1)

    if options.q:
        path = nvr.server.funcs.fnameescape(os.environ['PWD'])
        nvr.server.command('lcd {}'.format(path))
        nvr.server.funcs.setqflist('[]')
        if options.q == '-':
            for line in sys.stdin:
                nvr.server.command("caddexpr '{}'".
                        format(line.rstrip().replace("'", "''").replace('|', '\|')))
        else:
            with open(options.q, 'r') as f:
                for line in f.readlines():
                    nvr.server.command("caddexpr '{}'".
                            format(line.rstrip().replace("'", "''").replace('|', '\|')))
        nvr.server.command('silent lcd -')
        nvr.server.command('cfirst')

    if options.c:
        for cmd in options.c:
            if cmd == '-':
                cmd = sys.stdin.read()
            nvr.server.command(cmd)

    wait_for_n_buffers = nvr.wait
    if wait_for_n_buffers > 0:
        exitcode = 0

        def notification_cb(msg, args):
            nonlocal wait_for_n_buffers
            nonlocal exitcode

            if msg == 'BufDelete':
                wait_for_n_buffers -= 1
                if wait_for_n_buffers == 0:
                    nvr.server.stop_loop()
                    exitcode = 0 if len(args) == 0 else args[0]
            elif msg == 'Exit':
                nvr.server.stop_loop()
                exitcode = args[0]

        def err_cb(error):
            nonlocal exitcode
            print(error, file=sys.stderr)
            nvr.server.stop_loop()
            exitcode = 1

        nvr.server.run_loop(None, notification_cb, None, err_cb)
        nvr.server.close()
        sys.exit(exitcode)

    nvr.server.close()


if __name__ == '__main__':
    main()

