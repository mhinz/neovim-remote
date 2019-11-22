# Installation

## The normal way

    $ pip3 install neovim-remote

On most systems this will install to `/usr/local/bin`, which is usually in $PATH
already. You're done.

If you get a _permission denied_ error, e.g. because it tried to install to
`/usr/bin`, **do not** use `sudo` to force it!

Use this instead:

    $ pip3 install --user neovim-remote

This will install to `~/.local/bin` (Linux) or `~/Library/Python/3.x/bin`
(macOS) which needs to be added to $PATH.

This will give you the correct location:

    $ python3 -c 'import site; print(site.USER_BASE)'

If `nvr` is not in your path and you installed Python with `asdf`, you might need
to reshim:

    $ pip3 install neovim-remote
    $ asdf reshim python

## From repo

If you want to test your own changes, it makes sense to put your local repo into
_develop mode_. That way your Python environment will use the repo directly and
you don't have to reinstall the package after each change:

    $ git clone https://github.com/mhinz/neovim-remote
    $ cd neovim-remote
    $ pip3 install -e .

Now, `pip3 list` will show the path to the local repo after the package version.

## From zip

Download the [zipped
sources](https://github.com/mhinz/neovim-remote/archive/master.zip) and install
install them with either `pip3 install master.zip` or by running `python3
setup.py install` in the unzipped directory.

