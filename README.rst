.. figure:: https://github.com/mhinz/neovim-remote/raw/master/pictures/nvr-logo.png
   :alt: Logo

-  `Intro <#intro>`__
-  `Installation <#installation>`__
-  `Usage <#usage>`__
-  `FAQ <#faq>`__
-  `Demos <#demos>`__

Intro
-----

**nvr** is a tool that helps controlling nvim processes.

It basically does two things:

1. adds back the ``--remote`` family of options (see ``man vim``)
2. helps controlling the current nvim from within ``:terminal``

To target a certain nvim process, you either use the ``--servername``
option or set the environment variable ``$NVIM_LISTEN_ADDRESS``.

Since ``$NVIM_LISTEN_ADDRESS`` is implicitely set by each nvim process,
you can call **nvr** from within Neovim (``:terminal``) without
specifying ``--servername``.

Installation
------------

::

    $ pip3 install neovim-remote

Usage
-----

Start a nvim process (which acts as a server) in one shell:

::

    $ NVIM_LISTEN_ADDRESS=/tmp/nvimsocket nvim

And do this in another shell:

.. code:: shell

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

See ``nvr -h`` for all options.

FAQ
---

**How to open directories?**

``:e /tmp`` opens a directory view via netrw. Netrw works by hooking
into certain events, ``BufEnter`` in this case (see ``:au FileExplorer``
for all of them).

Unfortunately Neovim's API doesn't trigger any autocmds on its own, so
simply ``nvr /tmp`` won't work. Meanwhile you can work around it like
this:

::

    $ nvr /tmp -c 'doautocmd BufEnter'

**Reading from stdin?**

Yes! E.g. ``echo "foo\nbar" | nvr -o -`` and ``cat file | nvr --remote -`` work
just as you would expect them to work.

**Exit code?**

If you use a `recent enough Neovim
<https://github.com/neovim/neovim/commit/d2e8c76dc22460ddfde80477dd93aab3d5866506>`__,
nvr will use the same exit code as the linked nvim.

E.g. ``nvr --remote-wait <file>`` and then ``:cquit`` in the linked nvim will
make nvr return with 1.

**Talking to nvr from Neovim?**

Imagine ``nvr --remote-wait file``. The buffer that represents "file" in Neovim
now has a local variable ``b:nvr``. It's a list of channels for each connected
nvr process.

If we wanted to create a command that disconnects all nvr processes with exit
code 1:

::

    command! Cquit
        \  if exists('b:nvr')
        \|   for chanid in b:nvr
        \|     silent! call rpcnotify(chanid, 'Exit', 1)
        \|   endfor
        \| endif

Demos
-----

*(Click on the GIFs to watch them full-size.)*

Using nvr from another shell: |Demo 1|

Using nvr from within `:terminal`: |Demo 2|

.. |Demo 1| image:: https://github.com/mhinz/neovim-remote/raw/master/pictures/demo1.gif
.. |Demo 2| image:: https://github.com/mhinz/neovim-remote/raw/master/pictures/demo2.gif

