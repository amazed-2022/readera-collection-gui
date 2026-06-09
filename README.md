# readera-collection-gui
An **unofficial GUI tool** for loading and viewing books and quotes stored in ReadEra backup files.

**Current version:** v2.1.0  
**License:** GNU GPL v3.0  
**Author:** amazed  
**Version history:** [CHANGELOG](CHANGELOG.md)

---
**Dependencies:** PySide6
- Website: https://www.qt.io/qt-for-python
- License: LGPL v3.0
---


## Introduction
This project is not affiliated with, endorsed by, or connected to ReadEra or its developers, this tool exists solely to help users work with their own exported data outside the app.

**ReadEra is an excellent Android reading application.
If you enjoy using it, please consider supporting the developers by purchasing the Premium version of the official app.**

---
## Installation
1. **Install PySide6** (only required for the PySide GUI): `pip install PySide6`
2. **Create a backup file** in the ReadEra app (Settings → Backup & Restore)
3. **Transfer backup file to your PC** (Google Drive, Gmail, etc.)
4. **Extract the `.bak` file into a folder**  
   (only `library.json` is needed; other files can be deleted)
5. **Place the project Python files** in the same folder as `library.json`
6. **Run one of the following:**
    - `mini-gui.py` (lightweight Tkinter version)
    - `readera-collection-gui.py` (full version)

  
## Usage

To use all features of `readera-collection-cli`, the following should be ensured:
- Books should have **consistent, readable filenames**, e.g.:  
 `Example Author - Example Title.epub`
- In the ReadEra app, books should be organized into **Collections** (which are basically folders), e.g. novels, sci-fi, etc.
- After finishing a book, it should be **marked as "Have read"** in the ReadEra app
- Books should include an **Author** in the _About Document_ page within the ReadEra app
  
  <img width="511" height="193" alt="kép" src="https://github.com/user-attachments/assets/d945ae8d-08a1-4ea7-acf7-fc10dbcbf1fc" />
- Books should include a text-based **Review** in the _About Document_ page, containing the following data **separated by semicolons**:  
 `publish date`;`rating`;`ratings count`;

  <img width="496" height="158" alt="kép" src="https://github.com/user-attachments/assets/265f1679-7e73-4a65-b8bc-48492c609600" />
  
  ([goodreads](https://www.goodreads.com/) can be used for info)

## User Interfaces
### mini-gui
Designed for quick, distraction-free usage.
- Built with `Tkinter` (standard library, no external dependencies)
- Lightweight version of the full application
- Shows remaining quotes counter in the header
- Provides basic functionality only:
  - Random quote
  - Delay author (checkbutton)
  - Print every quote from a selected book
  - Clear output
  - Reset state

<p align="center">
<img width="640" alt="image" src="https://github.com/user-attachments/assets/9f256bce-4d9e-437e-8dd4-1404e8909c1a" />
</p>

### full-gui
Designed for full exploration and analysis.
- Full-featured GUI built with `PySide6`
- Print quotes of any length or only short quotes using corresponding buttons  
  (Use "delay author" toggle button to delay author display for each quote)
- Print all quotes from a selected book
- View quote distribution for a book (length/page mapping)
- View statistics
- Search within quote text
- Display books sorted by selected properties

<p align="center">
<img width="800" alt="kép" src="https://github.com/user-attachments/assets/7eaa9cef-f822-4603-b012-b60aa07a4d90" />
</p>


## License
This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.  
Copyright (C) amazed 2026.

This software is free to use, modify, and distribute under the terms of the GPL-3.0.  
You should have received a copy of the GNU General Public License along with this program.  
If not, see [GPL-3.0 License](https://www.gnu.org/licenses/gpl-3.0.html).
