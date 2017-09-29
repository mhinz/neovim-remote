# neovim-remote

[![Build status](https://travis-ci.org/mhinz/neovim-remote.svg?branch=master)](https://travis-ci.org/mhinz/neovim-remote)
[![Wheel?](https://img.shields.io/pypi/wheel/neovim-remote.svg)](https://pypi.python.org/pypi/neovim-remote)
[![PyPI version](https://img.shields.io/pypi/v/neovim-remote.svg)](https://pypi.python.org/pypi/neovim-remote)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/neovim-remote.svg)](https://pypi.python.org/pypi/neovim-remote)
[![License](https://img.shields.io/pypi/l/neovim-remote.svg)](https://pypi.python.org/pypi/neovim-remote)

- [Intro](#intro)
- [Use case](#use-case)
- [Installation](#installation)
- [Usage](#usage)
- [Demos](#demos)
- [FAQ](#faq)

## Intro

**nvr** is a tool that helps controlling nvim processes.

It does two things:

1. adds back the `--remote` family of options (see `man vim`)
2. helps controlling the current nvim from within `:terminal`

To target a specific nvim process, use either the `--servername` option or set
the environment variable `$NVIM_LISTEN_ADDRESS`.

If the targeted address does not exist, nvr starts a new process on its own by
running "nvim". You can change the command by setting `$NVR_CMD`.

Since `$NVIM_LISTEN_ADDRESS` is implicitely set by each nvim process, you can
call **nvr** from within Neovim (`:terminal`) without specifying `--servername`.

*NOTE: This tool relies on the Unix forking model, and thus Windows is not
supported.*

## Use case

Imagine Neovim is set as your default editor: `EDITOR=nvim`.

Now run `git commit`. In a regular shell, a new nvim process starts. In a
terminal buffer (`:terminal`), a new nvim process starts as well. Now you have
one nvim nested within another. You don't want that. Put this in your vimrc:

```vim
if has('nvim')
  let $VISUAL = 'nvr -cc split --remote-wait'
endif
```

That way, you get a new window for entering the commit message instead of a
nested nvim process.

Alternatively, you can make git always using nvr. In a regular shell, nvr will
create a new nvim process. In a terminal buffer, nvr will open a new buffer.

    $ git config --global core.editor 'nvr --remote-wait-silent'

## Installation

See [INSTALLATION.md](INSTALLATION.md)

## Usage

Start a nvim process (which acts as a server) in one shell:

    $ NVIM_LISTEN_ADDRESS=/tmp/nvimsocket nvim

And do this in another shell:

```sh
$ # Spares us from using --servername all the time:
$ export NVIM_LISTEN_ADDRESS=/tmp/nvimsocket
$ # This is optional, since nvr assumes /tmp/nvimsocket by default.

$ # Open two files:
$ nvr --remote file1 file2

$ # Send keys to the current buffer:
$ nvr --remote-send 'iabc<esc>'
$ # Enter insert mode, insert 'abc', and go back to normal mode again.

$ # Evaluate any VimL expression, e.g. get all listed buffers:
$ nvr --remote-expr "join(sort(map(filter(range(bufnr('$')), 'buflisted(v:val)'), 'bufname(v:val)')), "\""\n"\"")"
.config/git/config
vim/vimrc
zsh/.zprofile
```

See `nvr -h` for all options.

## Demos

_(Click on the GIFs to watch them full-size.)_

Using nvr from another shell: ![Demo 1](https://github.com/mhinz/neovim-remote/raw/master/images/demo1.gif)

Using nvr from within `:terminal`: ![Demo 2](https://github.com/mhinz/neovim-remote/raw/master/images/demo2.gif)

## FAQ

**How to open directories?**

`:e /tmp` opens a directory view via netrw. Netrw works by hooking into certain
events, `BufEnter` in this case (see `:au FileExplorer` for all of them).

Unfortunately Neovim's API doesn't trigger any autocmds on its own, so simply
`nvr /tmp` won't work. Meanwhile you can work around it like this:

    $ nvr /tmp -c 'doautocmd BufEnter'

**Reading from stdin?**

Yes! E.g. `echo "foo\nbar" | nvr -o -` and `cat file | nvr --remote -` work just
as you would expect them to work.

**Exit code?**

If you use a [recent enough
Neovim](https://github.com/neovim/neovim/commit/d2e8c76dc22460ddfde80477dd93aab3d5866506), nvr will use the same exit code as the linked nvim.

E.g. `nvr --remote-wait <file>` and then `:cquit` in the linked nvim will make
nvr return with 1.

**Talking to nvr from Neovim?**

Imagine `nvr --remote-wait file`. The buffer that represents "file" in Neovim
now has a local variable `b:nvr`. It's a list of channels for each connected nvr
process.

If we wanted to create a command that disconnects all nvr processes with exit
code 1:

```vim
command! Cquit
    \  if exists('b:nvr')
    \|   for chanid in b:nvr
    \|     silent! call rpcnotify(chanid, 'Exit', 1)
    \|   endfor
    \| endif
```

