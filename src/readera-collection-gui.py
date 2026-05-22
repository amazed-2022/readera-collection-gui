#=================================================
# IMPORT
#=================================================
import book_utils
import re
import sys

from book_collection import BookCollection, Book
from book_statistics import Statistics, StatisticsReporter
from constants_loader import constants
from collections import Counter
from datetime import datetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QStandardItem, QStandardItemModel, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextOption
from PySide6.QtWidgets import (
    QApplication, QComboBox, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QInputDialog, QMainWindow, QMessageBox, QPushButton, QSizePolicy, QStackedWidget,
    QVBoxLayout, QTableView, QTextEdit, QWidget
)
from quote_manager import QuoteManager, QuoteManagerUI

#=================================================
# MAIN WINDOW
#=================================================
class MainWindow(QMainWindow, QuoteManagerUI):

    #=================================================
    # type hints
    #=================================================
    collection: BookCollection
    quote_manager: QuoteManager

    filtered_books: list[str]
    authors_with_quotes: list[str]

    #===================
    # output state
    #===================
    output_font_size: int
    line_height_percent: int

    #===================
    # UI elements
    #===================
    panel: QWidget
    folders_dropdown: QComboBox
    authors_dropdown: QComboBox
    books_dropdown: QComboBox
    mode_dropdown: QComboBox

    delay_author_toggle: QPushButton
    buttons: dict[str, QPushButton]
    btn_increase: QPushButton
    btn_decrease: QPushButton

    output_stack: QStackedWidget
    text_output: QTextEdit
    table_output: QTableView

    #=================================================
    # initialization
    #=================================================
    def __init__(self, collection: BookCollection):
        super().__init__()

        #=================================================
        # instance attributes
        #=================================================
        self.collection = collection
        self.quote_manager = QuoteManager(self)
        self.filtered_books = []
        self.authors_with_quotes = []

        #=================================================
        # call init and build functions
        #=================================================
        self._init_window()
        self._init_data()
        self._init_state()
        self._init_filters()
        self._init_actions()
        self._init_signals()
        self._init_output()
        self._build_main_layout()
        self.show()

    #=================================================
    # init window
    #=================================================
    def _init_window(self):
        self.setWindowTitle(constants.GUI_TITLE)
        self.resize(*constants.WINDOW_SIZE)

        self.panel = QWidget()
        self.setCentralWidget(self.panel)

    #=================================================
    # data preparation
    #=================================================
    def _init_data(self):
        authors_set = set()

        # filtered books start with full list
        for book in self.collection.books:
            if book.total_quotes > 0:
                self.filtered_books.append(book.title)
                authors_set.add(book.author)

        # sorted returns a list
        self.authors_with_quotes = sorted(authors_set)

    #=================================================
    # default state
    #=================================================
    def _init_state(self):
        self.output_font_size = constants.DEFAULT_OUTPUT_FONT_SIZE
        self.line_height_percent = constants.DEFAULT_LINE_SPACING_HEIGHT

    #=================================================
    # ComboBox filters (dropdowns)
    #=================================================
    def _init_filters(self):
        self.folders_dropdown = QComboBox()
        self.authors_dropdown = QComboBox()
        self.books_dropdown = QComboBox()
        self.folders_dropdown.addItems([constants.ANY_FOLDER] + sorted(list(self.collection.folders.keys())))
        self.authors_dropdown.addItems([constants.ANY_AUTHOR] + self.authors_with_quotes)
        self.books_dropdown.addItems([constants.ANY_BOOK] + self.filtered_books)

        # increase font size for dropdowns
        font = self.folders_dropdown.font()
        font.setPointSize(font.pointSize() + 1)

        for cb in (self.folders_dropdown, self.authors_dropdown, self.books_dropdown):
            cb.setCurrentIndex(0)
            # for closed combobox text
            cb.setFont(font)
            # for dropdown list items
            cb.view().setFont(font)

    #=================================================
    # actions, adjustment
    #=================================================
    def _init_actions(self):
        self.delay_author_toggle = QPushButton("Random quotes: delay author")
        self.delay_author_toggle.setCheckable(True)
        self.delay_author_toggle.setChecked(False)
        self.delay_author_toggle.setToolTip("ON: Author appears after a delay\nOFF: Author appears immediately")
        self.delay_author_toggle.setStyleSheet("""
            QPushButton { background-color: none; }
            QPushButton:checked { background-color: rgb(180,230,180); }
        """)

        self.buttons = {
            "random": QPushButton("Random quote"),
            "every": QPushButton("Print every quote"),
            "stats": QPushButton("Statistics"),
            "short": QPushButton("Random short quote"),
            "dist": QPushButton("Quote distribution"),
            "search": QPushButton("Search"),
            "clear": QPushButton("Clear window"),
            "list": QPushButton("Book list"),
        }

        # adjustment buttons
        self.btn_increase = QPushButton("▲")
        self.btn_decrease = QPushButton("▼")

        self.mode_dropdown = QComboBox()
        self.init_mode_dropdown()

        for w in (self.btn_increase, self.btn_decrease, self.mode_dropdown):
            w.setFixedWidth(160)
            w.setMinimumHeight(40)

        # grab the font of first button (from dictionary list)
        font = self.buttons["random"].font()
        font.setPointSize(font.pointSize() + 1)

        for btn in (
            *self.buttons.values(),
            self.btn_increase,
            self.btn_decrease,
            self.delay_author_toggle
        ):
            btn.setFont(font)
            btn.setMinimumHeight(40)

    #=================================================
    # signals
    #=================================================
    def _init_signals(self):
        # only the function reference is bound here (no call operator "()" added)
        # the folder/author choice event triggers the authors and book lists update
        self.folders_dropdown.currentIndexChanged.connect(self.on_folder_or_author_change)
        self.authors_dropdown.currentIndexChanged.connect(self.on_folder_or_author_change)
        self.delay_author_toggle.toggled.connect(self.quote_manager.on_delay_author_toggle)

        # use lambda to defer immediate execution when an argument is passed
        self.buttons["random"].clicked.connect(self.quote_manager.print_random_quote)
        self.buttons["short"].clicked.connect(lambda: self.quote_manager.print_random_quote("short"))
        self.buttons["every"].clicked.connect(self.quote_manager.print_every_quote)
        self.buttons["stats"].clicked.connect(self.print_statistics)
        self.buttons["dist"].clicked.connect(self.print_quote_distribution)
        self.buttons["search"].clicked.connect(self.search)
        self.buttons["clear"].clicked.connect(self.clear)
        self.buttons["list"].clicked.connect(self.update_book_list_table)
        self.btn_increase.clicked.connect(lambda: self.on_adjust_button("increase"))
        self.btn_decrease.clicked.connect(lambda: self.on_adjust_button("decrease"))

    #===============
    # header layout
    # +----------------------------------------------------------------------------------------------+
    # | dropdown_layout (QGridLayout 3x2)    |      logo widget                                      |
    # +----------------------------------------------------------------------------------------------+
    # |  FOLDER      [folders]               |  fixed      |   ====================    |  fixed      |
    # |  AUTHOR      [authors]               |  margin     |   == The Collection ==    |  margin     |
    # |  BOOK        [books]                 |             |   ====================    |             |
    # +----------------------------------------------------------------------------------------------+
    def _build_header_layout(self):
        dropdown_layout = QGridLayout()
        # add left padding and space between columns
        dropdown_layout.setContentsMargins(30, 0, 0, 0)
        dropdown_layout.setHorizontalSpacing(30)

        # addWidget(widget, row, column, rowSpan, columnSpan, alignment)
        label = QLabel("FOLDER")
        label.setFont(QFont("Consolas", 12))
        dropdown_layout.addWidget(label, 0, 0)
        dropdown_layout.addWidget(self.folders_dropdown, 0, 1)
        label = QLabel("AUTHOR")
        label.setFont(QFont("Consolas", 12))
        dropdown_layout.addWidget(label, 1, 0)
        dropdown_layout.addWidget(self.authors_dropdown, 1, 1)
        label = QLabel("BOOK")
        label.setFont(QFont("Consolas", 12))
        dropdown_layout.addWidget(label, 2, 0)
        dropdown_layout.addWidget(self.books_dropdown, 2, 1)
        # labels fixed, dropdowns expand
        dropdown_layout.setColumnStretch(0, 0)
        dropdown_layout.setColumnStretch(1, 1)

        string = f"== The Collection =="
        the_collection_logo = f"{'=' * len(string)}\n{string}\n{'=' * len(string)}"
        logo_text = QLabel(the_collection_logo)
        logo_text.setFont(QFont("Consolas", 14))
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_text.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        logo_text.setContentsMargins(100, 0, 100, 0)

        header_layout = QHBoxLayout()
        header_layout.addLayout(dropdown_layout, 1)
        header_layout.addWidget(logo_text)
        header_layout.setContentsMargins(0, 10, 0, 10)

        return header_layout

    #=================================================
    # output stack
    #=================================================
    def _init_output(self):
        # stacked widget for text and table view
        self.output_stack = QStackedWidget()

        # text output
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setFont(QFont("Consolas", self.output_font_size))
        self.text_output.setStyleSheet("""
            QTextEdit {
                background-color: rgb(240,230,200);
                color: rgb(30, 28, 24);
                selection-background-color: rgb(205, 215, 185);
                selection-color: rgb(40, 35, 25);
            }
        """)
        self.text_output.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.text_output.document().setDocumentMargin(30)

        # column output, set colors
        self.table_output = QTableView()
        self.table_output.setStyleSheet("""
            QTableView {
                background-color: rgb(240,230,200);
                gridline-color: gray;
            }
            QTableView::item {
                background-color: rgb(240,230,200);
                color: rgb(30, 28, 24);
            }
            QTableView::item:selected {
                background-color: rgb(205, 215, 185);
                color: rgb(30, 28, 24);
            }
            QHeaderView::section {
                background-color: rgb(220,210,180);
                padding: 4px;
                border: 1px solid gray;
            }
        """)

        self.table_output.setSortingEnabled(True)
        self.table_output.setAlternatingRowColors(True)
        self.table_output.horizontalHeader().setStretchLastSection(True)
        self.table_output.verticalHeader().setVisible(False)
        self.table_output.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_output.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # first added gets index 0 (shown by default)
        self.output_stack.addWidget(self.text_output)
        self.output_stack.addWidget(self.table_output)

    def show_text_output(self):
        self.output_stack.setCurrentWidget(self.text_output)

    def show_table_output(self):
        self.output_stack.setCurrentWidget(self.table_output)
        self.table_output.resizeColumnsToContents()

    #=============
    # button grid
    # +-------------------------------------------------------------------------------------------+
    # | Random quote          | Print every quote     | Statistics            |         ▲         |
    # |-----------------------|-----------------------|-----------------------|-------------------|
    # | Random short quote    | Quote distribution    | Search                |   mode_dropdown   |
    # |-----------------------|-----------------------|-----------------------|-------------------|
    # | Delay author toggle   | Clear window          | Book list by property |         ▼         |
    # +-------------------------------------------------------------------------------------------+
    def _build_button_grid(self):
        button_grid = QGridLayout()

        widgets = [
            self.buttons["random"], self.buttons["every"], self.buttons["stats"], self.btn_increase,
            self.buttons["short"],  self.buttons["dist"],  self.buttons["search"], self.mode_dropdown,
            self.delay_author_toggle, self.buttons["clear"], self.buttons["list"], self.btn_decrease,
        ]

        positions = [(i, j) for i in range(3) for j in range(4)]
        for pos, w in zip(positions, widgets):
            button_grid.addWidget(w, pos[0], pos[1])

        return button_grid

    #=============
    # main_layout
    # +-------------------------------------------------+
    # | header_layout (dropdowns left, logo right)      |
    # +-------------------------------------------------+
    # | output_widget (text output)                     |
    # +-------------------------------------------------+
    # | grid_layout (3x4 buttons)                       |
    # +-------------------------------------------------+
    # | reset_button (full-width reset button)          |
    # +-------------------------------------------------+
    def _build_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.addLayout(self._build_header_layout())
        main_layout.addWidget(self.output_stack, 1)
        main_layout.addLayout(self._build_button_grid())
        self.output_stack.setCurrentIndex(0)

        reset = QPushButton("Reset")
        reset.setFont(self.buttons["random"].font())
        reset.setMinimumHeight(36)
        reset.setStyleSheet("background-color: rgb(220,220,220);")
        reset.setToolTip("Reset all settings and clear the output")
        reset.clicked.connect(self.reset)

        main_layout.addWidget(reset)
        self.panel.setLayout(main_layout)

    #=================================================
    # FUNCTION: folder/author dropdown change
    #=================================================
    def on_folder_or_author_change(self):
        chosen_folder = self.folders_dropdown.currentText()
        chosen_author = self.authors_dropdown.currentText()

        # gets the trigger widget, update authors dropdown if folder changed
        if self.sender() == self.folders_dropdown:
            if chosen_folder == constants.ANY_FOLDER:
                # use full list (again)
                authors = [constants.ANY_AUTHOR] + self.authors_with_quotes
            else:
                # build list based on current folder (set comprehension)
                folder_authors = {
                    book.author
                    for book in self.collection.books
                    if book.folder == chosen_folder and book.total_quotes > 0
                }
                folder_authors = sorted(folder_authors)
                authors = [constants.ANY_AUTHOR] + folder_authors

            self.authors_dropdown.clear()
            self.authors_dropdown.addItems(authors)
            self.authors_dropdown.setCurrentIndex(0)
            chosen_author = constants.ANY_AUTHOR

        # update books based on current folder and author
        self.filtered_books = [constants.ANY_BOOK]
        for book in self.collection.books:
            if chosen_folder != constants.ANY_FOLDER and book.folder != chosen_folder:
                continue
            if chosen_author != constants.ANY_AUTHOR and book.author != chosen_author:
                continue
            if book.total_quotes > 0:
                self.filtered_books.append(book.title)

        self.books_dropdown.clear()
        self.books_dropdown.addItems(self.filtered_books)
        self.books_dropdown.setCurrentIndex(0)

    #=================================================
    # FUNCTION: adjust buttons function
    #=================================================
    def on_adjust_button(self, direction):
        delta = 1 if direction == "increase" else -1

        if "Font" in self.mode_dropdown.currentText():
            self.output_font_size = min(20, max(10, self.output_font_size + delta))
            self.text_output.setFont(QFont("Consolas", self.output_font_size))
        elif "Line" in self.mode_dropdown.currentText():
            self.line_height_percent = min(200, max(100, self.line_height_percent + 10 * delta))
            self.set_output_line_height(self.line_height_percent)

        # ensure the last line is visible
        self.scroll_to_bottom()
        # value was changed, update dropdown text
        self.update_mode_dropdown_text()

    def _mode_dropdown_items(self):
        return [
            f"Font size: {self.output_font_size}",
            f"Line spacing: {self.line_height_percent} %",
        ]

    def init_mode_dropdown(self):
        self.mode_dropdown.addItems(self._mode_dropdown_items())

    def update_mode_dropdown_text(self):
        for i, text in enumerate(self._mode_dropdown_items()):
            self.mode_dropdown.setItemText(i, text)

    #=================================================
    # FUNCTION: log messages to the text box
    #=================================================
    def log(self, message, scroll_to_bottom: bool = True):
        # make sure text output is visible
        self.show_text_output()
        # use insertPlainText to prevent automatic scrolling
        self.text_output.insertPlainText(message + "\n")
        self.set_output_line_height(self.line_height_percent)
        if scroll_to_bottom:
            self.scroll_to_bottom()

    def set_output_line_height(self, line_height_percent):
        cursor = self.text_output.textCursor()
        cursor.beginEditBlock()

        # iterate over all blocks in the document
        block = self.text_output.document().firstBlock()
        while block.isValid():
            # select block
            cursor.setPosition(block.position())
            cursor.setPosition(block.position() + block.length() - 1, QTextCursor.MoveMode.KeepAnchor)

            # apply formatting
            block_fmt = QTextBlockFormat()
            block_fmt.setLineHeight(line_height_percent, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
            cursor.setBlockFormat(block_fmt)

            # move to the next paragraph (QTextBlock)
            block = block.next()

        cursor.endEditBlock()

    #=================================================
    # FUNCTION: update book list
    #=================================================
    def update_book_list_table(self):
        # get user input
        book_property = self._get_selected_book_property()
        if not book_property:
            return

        # build headers based on input
        headers, displayed_indexes = self._build_headers(book_property)

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([headers[i] for i in displayed_indexes])

        # get filtered book instances
        for book in self._get_filtered_books(book_property):
            row = self._build_row_items(book, book_property, displayed_indexes)
            if row:
                model.appendRow(row)

        self.table_output.setModel(model)
        self.table_output.clearSelection()
        self.table_output.scrollToTop()
        self.show_table_output()

    def _get_selected_book_property(self):
        prop, ok = QInputDialog.getItem(
            self,
            "Book List",
            "Select list option:",
            constants.PROPERTIES,
            0,
            False
        )
        return prop if ok else None

    @staticmethod
    def _build_headers(book_property):
        headers = [
            "" if book_property != constants.PROP_READ_DURATION else "Read duration",
            "" if book_property != constants.PROP_READ_DURATION else "Pages / day",
            "Author",
            "Title",
            "Year",
            "Rating",
            "Ratings x1000",
            "Folder",
            "Quotes",
            "Pages",
            "Quotes / pages",
            "Finished",
            "Added",
        ]
        # keep only non-empty headers and keep track of indexes
        indexes = [i for i, h in enumerate(headers) if h]
        return headers, indexes

    def _get_filtered_books(self, book_property):
        folder = self.folders_dropdown.currentText()

        books = (
            self.collection.books
            if folder == constants.ANY_FOLDER
            else [b for b in self.collection.books if b.folder == folder]
        )
        # further filter books based on selected property
        if book_property == constants.PROP_READING_NOW:
            return [b for b in books if b.activity_time and not b.is_read]

        if book_property == constants.PROP_FINISHED_LIST:
            return [b for b in books if b.is_read]

        if book_property == constants.PROP_READ_DURATION:
            return sorted(
                (b for b in books if b.is_read),
                key=lambda b: b.first_q_timestamp,
                reverse=True
            )

        return books

    def _build_row_items(self, book, book_property, displayed_indexes):
        if book_property == constants.PROP_READ_DURATION:
            duration, pages_per_day = self._get_read_duration_data(book)
            if not duration:
                return None
        else:
            duration, pages_per_day = "", 0

        row_data = [
            duration,
            pages_per_day,
            book.author,
            book.title.split("-", 1)[-1].strip(),
            int(book.published_date),
            float(book.rating),
            book.ratings_count,
            book.folder,
            int(book.total_quotes),
            int(book.pages_count),
            book.quotes_per_page,
            book.have_read_date.strftime('%Y-%b-%d') if book.is_read else "-",
            book.file_modified_date.strftime('%Y-%b-%d'),
        ]

        items = []
        for i in displayed_indexes:
            item = QStandardItem()
            value = row_data[i]

            is_number = isinstance(value, (int, float))

            item.setData(
                value if is_number else str(value),
                Qt.ItemDataRole.DisplayRole
            )

            item.setTextAlignment(
                (Qt.AlignmentFlag.AlignRight if is_number else Qt.AlignmentFlag.AlignLeft)
                | Qt.AlignmentFlag.AlignVCenter
            )
            item.setEditable(False)
            items.append(item)

        return items

    @staticmethod
    def _get_read_duration_data(book):
        if (book.first_q_timestamp <= constants.START_DATE_FOR_READ_LIST or
            (book.last_q_timestamp - book.first_q_timestamp) <= constants.ONE_DAY_IN_SECONDS or
            book.title in constants.EXCLUDED_TITLES_FROM_READ_DURATION):
            return "", 0

        # compute elapsed days if needed
        dt_first = datetime.fromtimestamp(book.first_q_timestamp)
        elapsed_days = (book.have_read_date - dt_first).days + 1

        if dt_first.year == book.have_read_date.year:
            duration_str = f"{dt_first.strftime('%Y %b.%d')} - {book.have_read_date.strftime('%b.%d')}"
        else:
            duration_str = f"{dt_first.strftime('%Y %b.%d')} - {book.have_read_date.strftime('%Y %b.%d')}"

        pages_per_day = int((book.pages_count / elapsed_days) + 0.5) if elapsed_days > 0 else 0

        # return tuple
        return duration_str, pages_per_day

    #=================================================
    # FUNCTION: clear
    #=================================================
    def clear(self):
        current = self.output_stack.currentWidget()

        if current is self.text_output:
            self.text_output.clear()
        elif current is self.table_output:
            model = self.table_output.model()
            if model:
                model.removeRows(0, model.rowCount())
                self.table_output.clearSelection()
                self.table_output.scrollToTop()

    #=================================================
    # FUNCTION: reset
    #=================================================
    def reset(self):
        # simple confirmation dialog in one line
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you sure you want to reset everything?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # reset QuoteManager state
        self.quote_manager.reset_state()

        # rebuild collection and reset dropdowns
        self.collection.build_the_collection()
        self.folders_dropdown.setCurrentIndex(0)
        self.authors_dropdown.setCurrentIndex(0)
        self.books_dropdown.setCurrentIndex(0)
        # build full dropdown lists again
        self.on_folder_or_author_change()

        # reset UI state
        self.delay_author_toggle.setChecked(False)
        self.clear()

        # reset font and layout settings
        self.output_font_size = constants.DEFAULT_OUTPUT_FONT_SIZE
        self.line_height_percent = constants.DEFAULT_LINE_SPACING_HEIGHT
        self.text_output.setFont(QFont("Consolas", self.output_font_size))

        # reset mode dropdown
        self.mode_dropdown.setCurrentIndex(0)
        self.update_mode_dropdown_text()

    #=================================================
    # shared helpers (QuoteManager + UI)
    #=================================================
    def clear_text_output(self) -> None:
        self.show_text_output()
        self.clear()

    def update_quotes_counter(self, use_book_total: bool = False) -> None:
        pass

    def set_quotes_counter(self, value: int) -> None:
        pass

    def delay_author_enabled(self) -> bool:
        return self.delay_author_toggle.isChecked()

    def schedule(self, ms: int, callback) -> QTimer:
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(callback)
        timer.start(ms)
        return timer

    def cancel_timer(self, timer: object) -> None:
        if isinstance(timer, QTimer) and timer.isActive():
            timer.stop()

    def scroll_to_top(self) -> None:
        cursor = self.text_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.text_output.setTextCursor(cursor)

    def scroll_to_bottom(self) -> None:
        cursor = self.text_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.text_output.setTextCursor(cursor)
        self.text_output.ensureCursorVisible()

    def get_collection_books(self) -> list[Book]:
        # provide a copy of the original list
        return list(self.collection.books)

    def get_filtered_books(self) -> list[str]:
        return self.filtered_books

    def get_selected_book_title(self) -> str:
        return self.books_dropdown.currentText()

    #=================================================
    # QUOTE FUNCTIONS (not supported by QuoteManager
    #=================================================
    #=================================================
    # FUNCTION: print quote distribution
    #=================================================
    def print_quote_distribution(self):
        self.clear()

        # get the book
        selected_title = self.get_selected_book_title()
        if selected_title == constants.ANY_BOOK:
            self.log("Select a book from the list.")
            return

        book = book_utils.get_book_by_title(self.collection.books, selected_title)

        if book is None:
            self.log("Book not found.")
            return

        title = book.title
        self.log(title)
        self.log("-" * len(title))
        self.log("")

        font_metrics = self.text_output.fontMetrics()
        avg_char_width = font_metrics.horizontalAdvance("X")
        # margin was added to the text output
        ctrl_width_px = self.text_output.width()-30
        columns = book_utils.calculate_columns_from_width(ctrl_width_px, avg_char_width)
        rows = round(columns * 0.14)
        space = "  "
        # get distribution using utils
        mapped_distribution = book_utils.compute_quote_distribution(book, columns=columns, rows=rows)
        # draw diagram
        self.log(f"{space}↑")
        for i in range(rows):
            row = ''.join('*' if mapped_distribution[j] >= (rows-i) else ' ' for j in range(columns))
            self.log(f"{space}|{row}")
        self.log(f"{space}{'-'*columns}→")
        self.log(f"{space}1{' '*(columns-len(str(book.pages_count))+1)}{book.pages_count}")

    #=================================================
    # FUNCTION: print statistics
    #=================================================
    def print_statistics(self):
        self.clear()
        reporter = StatisticsReporter()
        reporter.report(
            stats=Statistics.from_collection(collection),
            collection=self.collection,
            max_short_quote_chars=constants.MAX_CHAR_IN_SHORT_QUOTE,
            omitted_words=constants.WORDS_TO_OMIT_FROM_SEARCH,
            write=self.log,
            top_n_words=30
        )

    #=================================================
    # FUNCTION: search in quotes
    #=================================================
    def search(self):
        # create normal/match text formats
        fmt_normal = QTextCharFormat()
        fmt_normal.setFontWeight(QFont.Weight.Normal)
        fmt_normal.clearBackground()

        fmt_match = QTextCharFormat()
        # fmt_match.setFontItalic(True)
        fmt_match.setFontWeight(QFont.Weight.Bold)

        # popup for user input
        text, ok = QInputDialog.getText(self, "Search", "Enter at least 3 characters:")
        if not ok:
            # user canceled
            return
        else:
            self.clear()

        # check length
        str_to_search = text.strip().lower()
        if len(str_to_search) < 3:
            self.log("Incorrect input. Please enter at least 3 characters.\n")
            return

        selected_title = self.get_selected_book_title()
        if selected_title == constants.ANY_BOOK:
            books = [book for book in self.collection.books if book.title in self.filtered_books]
        else:
            book = book_utils.get_book_by_title(self.collection.books, selected_title)
            books = [book] if book else []

        counter = 0
        for book in books:
            match_in_book = False
            for quote in book.get_all_quotes_list():
                quote_text = quote.text.lower()
                if str_to_search in quote_text:
                    if not match_in_book:
                        self.log(f"{book.title}\n{'-'*len(book.title)}")
                        match_in_book = True
                    self.log('\n')
                    self.highlight(quote.text, str_to_search, fmt_normal, fmt_match)
                    counter += len(re.findall(str_to_search, quote_text))

        # print result summary
        result = f"\nMatched {counter} time{'s' if counter != 1 else ''}."
        self.log(result if counter else "No match found.")
        if counter:
            self.log('-'*len(result))


    def highlight(self, text, term, fmt_normal, fmt_match):
        cursor = self.text_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        pattern = re.compile(re.escape(term), re.IGNORECASE)
        last_pos = 0

        for match in pattern.finditer(text):
            # insert text before match (normal) and match with modified
            cursor.insertText(text[last_pos:match.start()], fmt_normal)
            cursor.insertText(text[match.start():match.end()], fmt_match)
            last_pos = match.end()

        # insert the remaining text after last match
        cursor.insertText(text[last_pos:], fmt_normal)
        cursor.insertText('\n')

#=================================================
# MAIN
#=================================================
if __name__ == "__main__":
    The_Collection = BookCollection()
    error = The_Collection.build_the_collection()
    app = QApplication(sys.argv)
    window = MainWindow(The_Collection)
    if error:
        window.log(f"Error reading JSON file: {error}")
    sys.exit(app.exec())
