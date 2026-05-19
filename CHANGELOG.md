# Changelog

All notable changes to this project will be documented in this file.

## [2.2.0] – 2026-XX
### mini-gui
#### Added
- Introduced `QuotePrinter` to separate quote printing logic from `MainWindow`
- Added `schedule()` and `cancel_timer()` abstraction in `MainWindow`
- Introduced `FilterPanel` to encapsulate dropdown UI logic in
  
#### Changed
- Refactored quote printing logic into `QuotePrinter` and removed direct UI/timer coupling
- Replaced direct `after/after_cancel` usage with abstracted scheduling API
- Refactored dropdown creation and selection handling into `FilterPanel`
- Moved combobox setup and value management from `MainWindow` to `FilterPanel`

---

## [2.1.0] – 2026-05
#### Added
- Quotes remaining counter to the header in `mini-gui`

#### Changed
- Removed global state and moved collection responsibility into `BookCollection`

---

## [2.0.0] – 2026-05
#### Added
- **mini-gui**
  - Uses built-in `tkinter` for a lightweight interface
  - Reduced functionality compared to the full version
  - Provides only basic navigation buttons

#### Changed
- Switched GUI framework from `wxPython` to `PySide6`
- Output is now a `QStackedWidget` (stacked view for multiple pages)
- Book lists are now table-based, allowing sortable rows
- Added font size and line spacing adjustment settings for improved readability
- Search results now highlight matching terms in **bold** for better visibility

---

## [1.1.0] – 2026-01
#### Added
- `is_read` property to `Book` for clearer read-status tracking
- Default read date as a configurable constant
- `constants_loader.py` to support local constants configuration

#### Changed
- Handles Zero Width Space characters in book titles during collection build
- Renamed variables to avoid date/timestamp confusion
- Improved internal variable naming consistency

#### Fixed
- Statistics printing issue
- Reset function issue

---

## [1.0.0] – 2026-01
#### Added
- Initial stable release
- Random quote printing (all quotes, by author, by folder)
- Book-based quote export
- Statistics and Search function
