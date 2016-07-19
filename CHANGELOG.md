# Change Log

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- Now it's possible to use `nvr --remote-wait` from within `:terminal`, without
  blocking until the nvim process ends, as long as `$NVIM_TERMINAL` is set. In
  that case, nvr will wait until the buffers opened via `--remote-wait` (or one
  of the other wait flags) get deleted before returning.

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

[Unreleased]: https://github.com/mhinz/neovim-remote/compare/v1.2...HEAD
[1.2]: https://github.com/mhinz/neovim-remote/compare/v1.1...v1.2
[1.1]: https://github.com/mhinz/neovim-remote/compare/v1.0...v1.1
[1.0]: https://github.com/mhinz/neovim-remote/compare/37d851b...v1.0
