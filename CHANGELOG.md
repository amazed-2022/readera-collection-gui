# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] – 2026-02
### Added
- **mini.gui**
  - Uses built-in tkinter for GUI
  - Reduced functionality compared to full version
  - Includes only basic buttons

### Changed
- Switched GUI framework from wxPython to PySide6
- Output is now a QStackedWidget (stacked view for multiple pages)
- Book lists are now table-based, so rows can be sorted in any order
- Added font size and line spacing adjustment settings for improved readability
- Search results now highlight matching terms in bold for easier visibility
  
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
