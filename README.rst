neovim-remote
=============

**nvr** is a tool that helps controlling nvim processes.

It basically does two things:

1. adds back the ``--remote`` family of options (see ``man vim``)
2. helps controlling the current nvim from within ``:terminal``

To target a certain nvim process, you either use the ``--servername`` option or
set the environment variable ``$NVIM_LISTEN_ADDRESS``.

Since ``$NVIM_LISTEN_ADDRESS`` is implicitely set by each nvim process, you can
call **nvr** from within Neovim (``:terminal``) without specifying
``--servername``.
