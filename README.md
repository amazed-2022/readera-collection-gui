# readera-collection-gui
An **unofficial GUI tool** for loading and viewing books and quotes stored in ReadEra backup files.

**Current version:** v1.1.0   
**License:** GNU GPL v3.0  
**Author:** amazed  
**Date:** Jan 2026  
[Version history](CHANGELOG.md)


---
**Dependencies:**
- wxPython
  - Website: https://www.wxpython.org/
  - License: wxWindows Library License
- PySide6
  - Website: https://www.qt.io/qt-for-python
  - License: LGPL v3.0
---


## Introduction
This project is not affiliated with, endorsed by, or connected to ReadEra or its developers, this tool exists solely to help users work with their own exported data outside the app.

**ReadEra is an excellent Android reading application.
If you enjoy using it, please consider supporting the developers by purchasing the Premium version of the official app.**

---
## Installation
1. **Install wxPython** separately `pip install wxPython`
2. **Create a backup file** in the ReadEra app (Settings / Backup & Restore)
3. **Transfer backup file to your PC** (Google Drive, Gmail, etc.)
4. **Unpack** `bak` file into a freely chosen folder (only `library.json` file will be needed, the rest can be deleted)
5. **Simply download** python files next to your extracted `library.json` file
6. **Run** `readera-collection-gui.py`

  
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


## Features / Highlights
- Print quotes of any length or only short quotes using corresponding buttons.
  (Use "delay author" toggle button to delay author print for each quote.)
- Print every quote from a selected book.
- Print quote distribution from a selected book (lengths/pages map).
- Print statistics.
- Search within quote text.
- Print a book list sorted by a selected property.

<img width="900" alt="kép" src="https://github.com/user-attachments/assets/0437fd7c-125d-469d-8dde-8eed7c2812a0" />



## License
This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.  
Copyright (C) amazed 2026.

This software is free to use, modify, and distribute under the terms of the GPL-3.0.  
You should have received a copy of the GNU General Public License along with this program.  
If not, see [GPL-3.0 License](https://www.gnu.org/licenses/gpl-3.0.html).
