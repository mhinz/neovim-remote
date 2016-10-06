# Change Log

All notable changes to this project will be documented in this file.

## [1.3] - 2016-10-06

- Many small fixes, code cleanups, and documentation improvements.
- The `--*wait*` family now works everywhere. It doesn't matter if nvr is run
  from the shell or from within :terminal. E.g. `nvr --remote-wait file1 file2`
  will block exactly until these two buffers got deleted (BufDelete). Or until
  nvim quits, of course.

## [1.2] - 2016-06-07

### Added

- Available on PyPI (`pip3 install neovim-remote`) as source distribution and
  [wheel](http://pythonwheels.com).
- Option: `-c` (execute single command).
- Option: `--remote-tab-{wait,silent,wait-silent}`.
- Support for TCP sockets.

### Changed

- `nvr` is a single file now.
- Option: `-wait` family actually waits now.
- Option: `--remote{,-silent,-wait,-wait-silent}` take `+{cmd}` anywhere in
  arguments.

## [1.1] - 2015-12-17

### Added

- `CHANGELOG.md` according to [keepachangelog.com](http://keepachangelog.com).
- Two GIFs showing off how to use nvr.
- Option: `--serverlist`
- Option: `-o` (open files via `:split`)
- Option: `-O` (open files via `:vsplit`)
- Option: `-p` (open files via `:tabedit`)
- Option: `-l` (switch to previous window via `:wincmd p`)
- Many bugfixes.

### Changed

- Renamed `nvim-remote.py` to `nvr` for convenience.
- nvr is no real wrapper anymore. This is done for implementing more useful
  options that act slight different than their nvim equivalents in the future.
- Unused arguments are fed to `--remote-silent`.

## [1.0] - 2015-12-16

First release!

[1.3]: https://github.com/mhinz/neovim-remote/compare/v1.2...v1.3.0
[1.2]: https://github.com/mhinz/neovim-remote/compare/v1.1...v1.2
[1.1]: https://github.com/mhinz/neovim-remote/compare/v1.0...v1.1
[1.0]: https://github.com/mhinz/neovim-remote/compare/37d851b...v1.0
