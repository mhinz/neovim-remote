# Change Log

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- Option: `-c` (execute single command)
- Option: `--remote-tab-{wait,silent,wait-silent}`.

### Changed

- Option: `--remote{,-silent,-wait,-wait-silent}` take `+{cmd}`
- Allow `+cmd` to be anywhere in the arguments.

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

[Unreleased]: https://github.com/mhinz/neovim-remote/compare/v1.1...HEAD
[1.1]: https://github.com/mhinz/neovim-remote/compare/v1.0...v1.1
[1.0]: https://github.com/mhinz/neovim-remote/compare/37d851b...v1.0
