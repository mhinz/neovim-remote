[![Build status](https://travis-ci.org/mhinz/neovim-remote.svg?branch=master)](https://travis-ci.org/mhinz/neovim-remote)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/neovim-remote.svg)](https://pypi.python.org/pypi/neovim-remote)

<div align='center'>
  <h1>neovim-remote</h1><br>
</div>

This package provides an executable called **nvr** which solves these cases:

- Controlling nvim processes from the shell. E.g. opening files in another
  terminal window.
- Opening files from within `:terminal` without starting a nested nvim process.

---

- [Installation](#installation)
- [Theory](#theory)
- [First steps](#first-steps)
- [Typical use cases](#typical-use-cases)
- [Demos](#demos)
- [FAQ](#faq)

---

## Installation

    pip3 install neovim-remote

If you encounter any issues, e.g. permission denied errors or you can't find the
`nvr` executable, read [INSTALLATION.md](INSTALLATION.md).

## Theory

Nvim always starts a server. Get its address via `:echo $NVIM_LISTEN_ADDRESS` or
`:echo v:servername`. Or specify an address at startup:
`NVIM_LISTEN_ADDRESS=/tmp/nvimsocket nvim`.

**nvr** will use `$NVIM_LISTEN_ADDRESS` or any address given to it via
`--servername`.

If the targeted address does not exist, **nvr** starts a new process by running
"nvim". You can change the command by setting `$NVR_CMD`. _(This requires
forking, so it won't work on Windows.)_

## First steps

Start a nvim process (which acts as a server) in one shell:

    NVIM_LISTEN_ADDRESS=/tmp/nvimsocket nvim

And do this in another shell:

```sh
# nvr uses /tmp/nvimsocket by default, so we're good.

# Open two files:
nvr --remote file1 file2

# Send keys to the current buffer:
nvr --remote-send 'iabc<esc>'
# Enter insert mode, insert 'abc', and go back to normal mode again.

# Evaluate any VimL expression, e.g. get the current buffer:
nvr --remote-expr 'bufname("")'
README.md
```

<details>
<summary>click here to see all nvr options</summary>

```
$ nvr -h
usage: nvr [arguments]

Remote control Neovim processes.

If no process is found, a new one will be started.

    $ nvr --remote-send 'iabc<cr><esc>'
    $ nvr --remote-expr 'map([1,2,3], "v:val + 1")'

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

optional arguments:
  -h, --help            show this help message and exit
  --remote [<file> [<file> ...]]
                        Use :edit to open files. If no process is found, throw
                        an error and start a new one.
  --remote-wait [<file> [<file> ...]]
                        Like --remote, but block until all buffers opened by
                        this option get deleted or the process exits.
  --remote-silent [<file> [<file> ...]]
                        Like --remote, but throw no error if no process is
                        found.
  --remote-wait-silent [<file> [<file> ...]]
                        Combines --remote-wait and --remote-silent.
  --remote-tab [<file> [<file> ...]]
                        Like --remote, but use :tabedit.
  --remote-tab-wait [<file> [<file> ...]]
                        Like --remote-wait, but use :tabedit.
  --remote-tab-silent [<file> [<file> ...]]
                        Like --remote-silent, but use :tabedit.
  --remote-tab-wait-silent [<file> [<file> ...]]
                        Like --remote-wait-silent, but use :tabedit.
  --remote-send <keys>  Send key presses.
  --remote-expr <expr>  Evaluate expression and print result in shell.
  --servername <addr>   Set the address to be used. This overrides the default
                        "/tmp/nvimsocket" and $NVIM_LISTEN_ADDRESS.
  --serverlist          Print the TCPv4 and Unix domain socket addresses of
                        all nvim processes.
  -cc <cmd>             Execute a command before every other option.
  -c <cmd>              Execute a command after every other option.
  -d                    Diff mode. Use :diffthis on all to be opened buffers.
  -l                    Change to previous window via ":wincmd p".
  -o <file> [<file> ...]
                        Open files via ":split".
  -O <file> [<file> ...]
                        Open files via ":vsplit".
  -p <file> [<file> ...]
                        Open files via ":tabedit".
  -q <errorfile>        Read errorfile into quickfix list and display first
                        error.
  -s                    Silence "no server found" message.
  -t <tag>              Jump to file and position of given tag.
  --nostart             If no process is found, do not start a new one.
  --version             Show the nvr version.

Development: https://github.com/mhinz/neovim-remote

Happy hacking!
```
</details>

## Typical use cases

- **Open files from within `:terminal` without starting a nested nvim process.**

    Easy-peasy! Just `nvr file`.

    This works without any prior setup, because `$NVIM_LISTEN_ADDRESS` is always
    set within Nvim. And `nvr` will default to that address.

    I often work with two windows next to each other. If one contains the
    terminal, I can use `nvr -l foo` to open the file in the other window.

- **Open files always in the same nvim process no matter which terminal you're in.**

    If you just run `nvr -s`, a new nvim process will start and set its address
    to `/tmp/nvimsocket` automatically.

    Now, no matter in which terminal you are, `nvr file` will always work on
    that nvim process. That is akin to `emacsclient` from Emacs.

- **Use nvr in plugins.**

    Some plugins rely on the `--remote` family of options from Vim. Nvim had to
    remove those when they switched to outsource a lot of manual code to libuv.
    These options are [planned to be added back](https://github.com/neovim/neovim/issues/1750), though.

    In these cases nvr can be used as a drop-in replacement. E.g.
    [vimtex](https://github.com/lervag/vimtex) can be configured to use nvr to
    jump to a certain file and line: [read](https://github.com/lervag/vimtex/blob/80b96c13fe9edc5261e9be104fe15cf3bdc3173d/doc/vimtex.txt#L1702-L1708).

- **Use nvr as git editor.**

    Imagine Neovim is set as your default editor via `$VISUAL` or `$EDITOR`.

    Running `git commit` in a regular shell starts a nvim process. But in a
    terminal buffer (`:terminal`), a new nvim process starts as well. Now you
    have one nvim nested within another.
    
    If you do not want this, put this in your vimrc:

    ```vim
    if has('nvim')
      let $GIT_EDITOR = 'nvr -cc split --remote-wait'
    endif
    ```

    That way, you get a new window for inserting the commit message instead of a
    nested nvim process. But git still waits for nvr to finish, so make sure to
    delete the buffer after saving the commit message: `:w | bd`.

    If you don't like using `:w | bd` and prefer the good old `:wq` (or `:x`),
    put the following in your vimrc:

    ```vim
    autocmd FileType gitcommit set bufhidden=delete
    ```

    To use nvr from a regular shell as well:

        $ git config --global core.editor 'nvr --remote-wait-silent'

- **Use nvr as git mergetool.**

    If you want to use nvr for `git difftool` and `git mergetool`, put this in
    your gitconfig:

    ```
    [diff]
        tool = nvr
    [difftool "nvr"]
        cmd = nvr -s -d $LOCAL $REMOTE
    [merge]
        tool = nvr
    [mergetool "nvr"]
        cmd = nvr -s -d $LOCAL $BASE $REMOTE $MERGED -c 'wincmd J | wincmd ='
    ```

    `nvr -d` is a shortcut for `nvr -d -O` and acts like `vim -d`, thus it uses
    `:vsplit` to open the buffers. If you want them to be opened via `:split`
    instead, use `nvr -d -o`.

    When used as mergetool and all four buffers got opened, the cursor is in the
    window containing the $MERGED buffer. We move it to the bottom via `:wincmd
    J` and then equalize the size of all windows via `:wincmd =`.

- **Use nvr for scripting.**

    You might draw some inspiration from [this Reddit
    thread](https://www.reddit.com/r/neovim/comments/aex45u/integrating_nvr_and_tmux_to_use_a_single_tmux_per).

## Demos

_(Click on the GIFs to watch them full-size.)_

Using nvr from another shell: ![Demo 1](https://github.com/mhinz/neovim-remote/raw/master/images/demo1.gif)

Using nvr from within `:terminal`: ![Demo 2](https://github.com/mhinz/neovim-remote/raw/master/images/demo2.gif)

## FAQ

- **How to open directories?**

    `:e /tmp` opens a directory view via netrw. Netrw works by hooking into certain
    events, `BufEnter` in this case (see `:au FileExplorer` for all of them).

    Unfortunately Neovim's API doesn't trigger any autocmds on its own, so simply
    `nvr /tmp` won't work. Meanwhile you can work around it like this:

        $ nvr /tmp -c 'doautocmd BufEnter'

- **Reading from stdin?**

    Yes! E.g. `echo "foo\nbar" | nvr -o -` and `cat file | nvr --remote -` work just
    as you would expect them to work.

- **Exit code?**

    If you use a [recent enough
    Neovim](https://github.com/neovim/neovim/commit/d2e8c76dc22460ddfde80477dd93aab3d5866506), nvr will use the same exit code as the linked nvim.

    E.g. `nvr --remote-wait <file>` and then `:cquit` in the linked nvim will make
    nvr return with 1.

- **How to send a message to all waiting clients?**

    If you open a buffer with any of the _wait_ options, that buffer will get a
    variable `b:nvr`. The variable contains a list of channels wheres each
    channel is a waiting nvr client.

    Currently nvr only understands the `Exit` message. You could use it to
    disconnect all waiting nvr clients at once:

    ```vim
    command! DisconnectClients
        \  if exists('b:nvr')
        \|   for client in b:nvr
        \|     silent! call rpcnotify(client, 'Exit', 1)
        \|   endfor
        \| endif
    ```

