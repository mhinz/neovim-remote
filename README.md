neovim-remote
-------------

- [Intro](#intro)
- [Installation](#installation)
- [Examples](#examples)
- [Demos](#demos)

## Intro

**nvr** is a tool that helps controlling nvim processes.

It basically does two things:

1. adds back the `--remote` family of options (see `man vim`)
1. helps controlling the current nvim from within `:terminal`

To target a certain nvim process, you either use the `--servername` option or
set the environment variable `$NVIM_LISTEN_ADDRESS`.

Since `$NVIM_LISTEN_ADDRESS` is implicitely set by each nvim process, you can
call **nvr** from within Neovim (`:terminal`) without specifying `--servername`.

## Installation

Assuming `~/bin` is in your `$PATH`:

**1)** Install the Python provider for Neovim:
```
$ pip3 install neovim
```

**2a)** Using the git repo:
```
$ mkdir -p ~/github
$ git clone https://github.com/mhinz/neovim-remote.git ~/github/neovim-remote
$ ln -s ~/github/neovim-remote/nvr ~/bin/nvr
```

**2b)** Download the script directly:
```
$ # Or alternatively:
$ curl -Lo ~/bin/nvr https://raw.githubusercontent.com/mhinz/neovim-remote/master/nvr
```

**3)**
```
$ chmod 700 ~/bin/nvr
```

## Examples

In one window, create the server process:
```
$ NVIM_LISTEN_ADDRESS=/tmp/nvimsocket nvim
```
In another window do this:
```shell
$ # Spares us from using --servername all the time:
$ export NVIM_LISTEN_ADDRESS=/tmp/nvimsocket
$ # Open 2 files in the server:
$ nvr --remote file1 --remote file2
$ # Send keys to the current buffer of the server:
$ # Enter insert mode, enter 'abc', and go back to normal mode again:
$ nvr --remote-send 'iabc<esc>'
$ # Evaluate any VimL expression.
$ # Get all listed buffers:
$ nvr --remote-expr "join(sort(map(filter(range(bufnr('$')), 'buflisted(v:val)'), 'bufname(v:val)')), "\""\n"\"")"
.config/git/config
vim/vimrc
zsh/.zprofile
```

See `nvr -h` for all options.

## Demos

(Click the GIFs to watch them fullscreen.)

Using nvr from a different window (another tmux pane in this case):
![Demo 1](https://github.com/mhinz/neovim-remote/raw/master/demos/demo1.gif)

Using nvr from within Neovim:
![Demo 2](https://github.com/mhinz/neovim-remote/raw/master/demos/demo2.gif)
