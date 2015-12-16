neovim-remote
-------------

Neovim was rewritten to be more modular than Vim. It comes with a fancy API that
lead to reduced code size in the core, but also obsoleted some often used
features.

One of those features is the `--remote` family of command-line arguments, which
is used to communicate with server instances.

But fear no more! The **nvr** helper tool emulates these *missing* arguments.

**Hint:** Technically every nvim instance is a server instance. If you want to
use an already running nvim process as the server, use `:echo v:servername` to
get the path to the unix socket used for communication. Afterwards do:
```
export NVIM_LISTEN_ADDRESS=/path/to/unix/socket
```

This way you can omit `--servername` in subsequent calls to **nvr**.

Since `$NVIM_LISTEN_ADDRESS` is implicitely set by each nvim instance, you can
call **nvr** from within Neovim (`:terminal`!) without specifying
`--servername` either.

Installation
------------

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

Examples
---------

In one window, create the server instance:
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

The help shows all supported arguments:
```
$ nvr -h
usage: nvr [arguments]

Helper tool for nvim that provides --remote and friends.

optional arguments:
  -h, --help            show this help message and exit
  --remote <file>       open file in new buffer [ASYNC]
  --remote-wait <file>  as --remote [SYNC]
  --remote-silent <file>
                        as --remote, but don't throw error if no server is
                        found [ASYNC]
  --remote-wait-silent <file>
                        as --remote, but don't throw error if no server is
                        found [SYNC]
  --remote-tab <file>   open file in new tab [SYNC]
  --remote-send <keys>  send keys to server [SYNC]
  --remote-expr <expr>  evaluate expression and print result [SYNC]
  --servername <sock>   path to unix socket (overrides $NVIM_LISTEN_ADDRESS)

Happy hacking!
```

