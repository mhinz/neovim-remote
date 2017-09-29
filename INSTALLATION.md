# Installation

#### The normal way

    $ pip3 install neovim-remote

On most systems this will be good enough.

If you get a "permission denied" error, don't use `sudo` to force it! Use
this instead:

    $ pip3 install --user neovim-remote

..and make sure that `~/.local/bin` is in $PATH.

#### From repo

If you want to test your own changes, it makes sense to put your local repo into
_develop mode_. That way your Python environment will use the repo directly and
you don't have to reinstall the package after each change:

    $ git clone https://github.com/mhinz/neovim-remote
    $ cd neovim-remote
    $ pip3 install -e .

Now, `pip3 list` will show the path to the local repo after the package version.

#### From zip

Download the [zipped
sources](https://github.com/mhinz/neovim-remote/archive/master.zip) and install
install them with either `pip3 install master.zip` or by running `python3
setup.py install` in the unzipped directory.

