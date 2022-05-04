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
import multiprocessing
import os
import re
import sys
import textwrap
import time
import traceback

import psutil
import pynvim

class Nvr():
    def __init__(self, address, silent=False):
        self.address = address
        self.server = None
        self.silent = silent
        self.wait = 0
        self.started_new_process = False
        self.handled_first_buffer = False
        self.diffmode = False

    def attach(self):
        try:
            socktype, address, port = parse_address(self.address)
            if socktype == 'tcp':
                self.server = pynvim.attach('tcp', address=address, port=int(port))
            else:
                self.server = pynvim.attach('socket', path=address)
        except OSError:
            # Ignore invalid addresses.
            pass

    def try_attach(self, args, nvr, options, arguments):
            for i in range(10):
                self.attach()
                if self.server:
                    self.started_new_process = True
                    return main2(nvr, options, arguments)
                time.sleep(0.2)
            print(f'[!] Unable to attach to the new nvim process. Is `{" ".join(args)}` working?')
            sys.exit(1)

    def execute_new_nvim_process(self, silent, nvr, options, arguments):
        if not silent:
            print(textwrap.dedent('''\
                [*] Starting new nvim process using $NVR_CMD or 'nvim'.

                    Use --nostart to avoid starting a new process.
            '''))

        args = os.environ.get('NVR_CMD')
        args = args.split(' ') if args else ['nvim']

        multiprocessing.Process(target=self.try_attach, args=(args, nvr, options, arguments)).start()

        os.environ['NVIM_LISTEN_ADDRESS'] = self.address
        try:
            os.execvpe(args[0], args, os.environ)
        except FileNotFoundError:
            print(f'[!] Can\'t start new nvim process: `{args[0]}` is not in $PATH.')
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
        self.server.command(f'{cmd} {path}')
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
        self.server.command(f'autocmd BufDelete <buffer> silent! call rpcnotify({chanid}, "BufDelete")')
        self.server.command(f'autocmd VimLeave * if exists("v:exiting") && v:exiting > 0 | silent! call rpcnotify({chanid}, "Exit", v:exiting) | endif')
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
                self.read_stdin_into_buffer(stdin_cmd(cmd))
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
            self.diffthis()

            if wait:
                self.wait_for_current_buffer()

        for cmd in cmds:
            self.server.command(cmd if cmd else '$')

        return len(files)


def stdin_cmd(cmd):
    return {
            'edit': 'enew',
            'split': 'new',
            'vsplit': 'vnew',
            'tabedit': 'tabnew',
            }[cmd]


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


def parse_args(argv):
    form_class = argparse.RawDescriptionHelpFormatter
    usage      = argv[0] + ' [arguments]'
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


def show_message(address):
    print(textwrap.dedent(f'''
        [!] Can't connect to: {address}

            The server (nvim) and client (nvr) have to use the same address.

            Server:

                Specify the server address when starting nvim:

                $ nvim --listen {address}

                Use `:echo v:servername` to verify the address.

                Alternatively, run nvr without arguments. It defaults to
                starting a new nvim process with the server name set to
                "/tmp/nvimsocket".

                Security: When using an Unix domain socket, that socket should
                have proper permissions so that it is only accessible by your
                user.

            Client:

                Expose $NVIM_LISTEN_ADDRESS (obsolete in nvim but still
                supported by nvr) to the environment before using nvr or use
                its --servername option. If neither is given, nvr assumes
                \"/tmp/nvimsocket\".

                $ NVIM_LISTEN_ADDRESS={address} nvr file1 file2
                $ nvr --servername {address} file1 file2
                $ nvr --servername 127.0.0.1:6789 file1 file2

            Use -s to suppress this message.
        '''))


def split_cmds_from_files(args):
    cmds = []
    files = []
    for _ in range(len(args)):
        if args[0][0] == '+':
            cmds.append(args.pop(0)[1:])
        elif args[0] == '--':
            args.pop(0)
            files += args
            break
        else:
            files.append(args.pop(0))
    return cmds, files


def print_versions():
    import pkg_resources
    print('nvr ' + pkg_resources.require("neovim-remote")[0].version)
    print('pynvim ' + pkg_resources.require('pynvim')[0].version)
    print('psutil ' + pkg_resources.require('psutil')[0].version)
    print('Python ' + sys.version.split('\n')[0])


def print_addresses():
    addresses = []
    errors = []

    for proc in psutil.process_iter(attrs=['name']):
        if proc.info['name'] == 'nvim':
            try:
                for conn in proc.connections('inet4'):
                    addresses.insert(0, ':'.join(map(str, conn.laddr)))
                for conn in proc.connections('inet6'):
                    addresses.insert(0, ':'.join(map(str, conn.laddr)))
                for conn in proc.connections('unix'):
                    if conn.laddr:
                        addresses.insert(0, conn.laddr)
            except psutil.AccessDenied:
                errors.insert(0, f'Access denied for nvim ({proc.pid})')

    for addr in sorted(addresses):
        print(addr)
    for error in sorted(errors):
        print(error, file=sys.stderr)


def parse_address(address):
    try:
        host, port = address.rsplit(':', 1)
        if port.isdigit():
            return 'tcp', host, port
        raise ValueError
    except ValueError:
        return 'socket', address, None


def main(argv=sys.argv, env=os.environ):
    options, arguments = parse_args(argv)

    if options.version:
        print_versions()
        return

    if options.serverlist:
        print_addresses()
        return

    address = options.servername or env.get('NVIM') or env.get('NVIM_LISTEN_ADDRESS') or '/tmp/nvimsocket'

    nvr = Nvr(address, options.s)
    nvr.attach()

    if not nvr.server:
        silent = options.remote_silent or options.remote_wait_silent or options.remote_tab_silent or options.remote_tab_wait_silent or options.s
        if not silent:
            show_message(address)
        if options.nostart:
            sys.exit(1)
        nvr.execute_new_nvim_process(silent, nvr, options, arguments)

    main2(nvr, options, arguments)


def main2(nvr, options, arguments):
    if options.d:
        nvr.diffmode = True

    if options.cc:
        for cmd in options.cc:
            if cmd == '-':
                cmd = sys.stdin.read()
            nvr.server.command(cmd)

    if options.l:
        nvr.server.command('wincmd p')

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
    elif arguments and options.d:
        # Emulate `vim -d`.
        options.O = arguments
        arguments = []

    if options.remote_send:
        nvr.server.input(options.remote_send)

    if options.remote_expr:
        result = ''
        if options.remote_expr == '-':
            options.remote_expr = sys.stdin.read()
        try:
            result = nvr.server.eval(options.remote_expr)
        except:
            print(textwrap.dedent(f"""
                No valid expression: {options.remote_expr}
                Test it in Neovim: :echo eval('...')
                If you want to execute a command, use -c or -cc instead.
            """))
        if type(result) is bytes:
            print(result.decode())
        elif type(result) is list:
            print(list(map(lambda x: x.decode() if type(x) is bytes else x, result)))
        elif type(result) is dict:
            print({ (k.decode() if type(k) is bytes else k): v for (k,v) in result.items() })
        else:
            result = str(result)
            if not result.endswith(os.linesep):
                result += os.linesep
            print(result, end='', flush=True)

    if options.o:
        args = options.o + arguments
        if nvr.diffmode and not nvr.started_new_process:
            nvr.fnameescaped_command('tabedit', args[0])
            nvr.execute(args[1:], 'split', silent=True, wait=False)
        else:
            nvr.execute(args, 'split', silent=True, wait=False)
        nvr.server.command('wincmd =')
    elif options.O:
        args = options.O + arguments
        if nvr.diffmode and not nvr.started_new_process:
            nvr.fnameescaped_command('tabedit', args[0])
            nvr.execute(args[1:], 'vsplit', silent=True, wait=False)
        else:
            nvr.execute(args, 'vsplit', silent=True, wait=False)
        nvr.server.command('wincmd =')
    elif options.p:
        nvr.execute(options.p + arguments, 'tabedit', silent=True, wait=False)
    else:
        # Act like --remote-silent by default.
        nvr.execute(arguments, 'edit', silent=True)

    if options.t:
        try:
            nvr.server.command('tag ' + options.t)
        except nvr.server.error as e:
            print(e)
            sys.exit(1)

    if options.q:
        path = nvr.server.funcs.fnameescape(os.environ['PWD'])
        nvr.server.command('lcd ' + path)
        nvr.server.funcs.setqflist([])
        if options.q == '-':
            for line in sys.stdin:
                nvr.server.command("caddexpr '{}'".
                        format(line.rstrip().replace("'", "''").replace('|', r'\|')))
        else:
            with open(options.q, 'r') as f:
                for line in f.readlines():
                    nvr.server.command("caddexpr '{}'".
                            format(line.rstrip().replace("'", "''").replace('|', r'\|')))
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

