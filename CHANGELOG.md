# Change Log

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- `CHANGELOG.md` according to [keepachangelog.com](http://keepachangelog.com).
- two GIFs showing off how to use nvr
- Option: `--serverlist`
- Option: `-o`
- Option: `-O`
- Option: `-p`
- Option: `-l`

### Changed
- Renamed `nvim-remote.py` to `nvr` for convenience.
- "nvr" is no real wrapper anymore. This is done for implementing more useful
  options that act slight different than their nvim equivalents in the future.
- Unused arguments are fed to `--remote-silent`.

## [1.0] - 2015-12-16
First release!

[Unreleased]: https://github.com/mhinz/neovim-remote/compare/v1.0...HEAD
[1.0]: https://github.com/mhinz/neovim-remote/compare/37d851b...v1.0
