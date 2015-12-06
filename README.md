nvim-remote
-----------

Neovim was rewritten to be more modular than Vim. It comes with a fancy API that
lead to reduced code size in the core, but also obsoleted some often used
features.

One of those features is the `--remote` family of command-line arguments, which
is used to communicate with server instances.

But fear no more! nvim-remote acts as a wrapper for nvim and emulates these
*missing* features. If none of the emulated arguments were given, it simply
starts `nvim` with all other arguments.

Thus you could make this wrapper a real nvim replacement à la `alias
nvim=nvim-remote.py`, if you like.

**Hint:** Technically every nvim instance is a server instance. If you want to
use an already running nvim process as the server, use `:echo v:servername` to
get the path to the unix socket used for communication. Afterwards do:
```
export NVIM_LISTEN_ADDRESS=/path/to/unix/socket
```

This way you can omit `--servername` in subsequent calls to nvim-remote.py.

Installation
------------

Assuming `~/bin` is in your `$PATH`:

**1)** Install the Neovim host for Python:
```
$ pip3 install neovim
```

**2a)** Using the git repo:
```
$ mkdir -p ~/github
$ git clone https://github.com/mhinz/nvim-remote.git ~/github/nvim-remote
$ ln -s ~/github/nvim-remote/nvim-remote.py ~/bin/nvim-remote.py
```

**2b)** Download the script directly:
```
$ # Or alternatively:
$ curl -Lo ~/bin/nvim-remote.py https://raw.githubusercontent.com/mhinz/nvim-remote/master/nvim-remote.py
```

**3)**
```
$ chmod 700 ~/bin/nvim-remote.py
```

Examples
---------

In one window, create the server instance:
```
$ nvim-remote.py --servername /tmp/nvimsocket
```
In another window do this:
```shell
$ # Spares us from using --servername all the time:
$ export NVIM_LISTEN_ADDRESS=/tmp/nvimsocket
$ # Open 2 files in the server:
$ nvim-remote.py --remote file1 --remote file2
$ # Send keys to the current buffer of the server:
$ # Enter insert mode, enter 'abc', and go back to normal mode again:
$ nvim-remote.py --remote-send 'iabc<esc>'
$ # Evaluate any VimL expression.
$ # Get the absolute path to the server's current buffer:
$ nvim-remote.py --remote-expr 'shellescape(expand("%:p"))'
'/Users/mhi/.dotfiles/vim/vimrc'
```

The help shows all supported arguments:
```
$ nvim-remote.py -h
usage: ./nvim-remote.py [arguments]

nvim wrapper that provides --remote and friends.

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

