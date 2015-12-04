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

Usage
-----

Imagine 2 windows running your favourite shell.

Server window: `nvim-remote.py --servername /tmp/nvimsocket`

Client window: `nvim-remote.py --servername /tmp/nvimsocket --remote file1 --remote file2`

**Hint**: Instead of specifying `--servername` all the time, you can also export
`NVIM_LISTEN_ADDRESS` instead.

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
  --serverlist          simply prints $NVIM_LISTEN_ADDRESS

Happy hacking!
```

