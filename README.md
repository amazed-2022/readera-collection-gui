# readera-collection-gui
An **unofficial GUI tool** for loading and viewing books and quotes stored in ReadEra backup files.

**Current version:** v1.0.0   
**License:** GNU GPL v3.0  
**Author:** amazed  
**Date:** Jan 2026  
[Version history](CHANGELOG.md)


---
**Dependencies:** wxPython
- Website: [https://www.wxpython.org/](https://www.wxpython.org/)
- License: wxWindows Library License
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
- Books should include a text-based **Review** in the _About Document_ page, containing the following data **separated by semicolons**:  
 `publish date`;`rating`;`ratings count`;  
  (I use data from [goodreads](https://www.goodreads.com/))


## Features / Highlights
### TBD

## License
This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.  
Copyright (C) amazed 2026.

This software is free to use, modify, and distribute under the terms of the GPL-3.0.  
You should have received a copy of the GNU General Public License along with this program.  
If not, see [GPL-3.0 License](https://www.gnu.org/licenses/gpl-3.0.html).
