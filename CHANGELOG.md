# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] – 2026-02
### Changed
- Changed GUI framework from wxPython to PySide6
  
## [1.1.0] – 2026-01
### Added
- `is_read` property to `Book` for clearer read-status tracking
- Default read date as a configurable constant
- `constants_loader.py` to support local constants configuration

### Changed
- Handles Zero Width Space characters in book titles during collection build
- Renamed variables to avoid date/timestamp confusion
- Improved internal variable naming consistency

### Fixed
- Statistics printing issue
- Reset function issue


## [1.0.0] – 2026-01
### Added
- Initial stable release
- Random quote printing (all quotes, by author, by folder)
- Book-based quote export
- Statistics and Search function
