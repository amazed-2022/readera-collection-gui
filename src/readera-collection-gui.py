#=================================================
# IMPORT
#=================================================
import book_collection
import book_utils
from constants_loader import constants
import datetime
import re
import sys
from collections import Counter

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QFont, QPainter, QStandardItem, QStandardItemModel, QTextBlockFormat,
    QTextCharFormat, QTextCursor, QTextOption
)
from PySide6.QtWidgets import (
    QApplication, QComboBox, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QInputDialog, QMainWindow, QMessageBox, QPushButton, QSizePolicy, QStackedWidget,
    QVBoxLayout, QTableView, QTextEdit, QWidget
)
from PyQt6.QtCharts import QBarSeries, QBarSet, QChart, QChartView, QValueAxis

#=================================================
# MAIN WINDOW
#=================================================
class MainWindow(QMainWindow):

    #=================================================
    # QMainWindow
    # +-- CentralWidget (self.panel)
    #     +-- QVBoxLayout (main_layout)
    #         +-- Header layout (QHBoxLayout)
    #         +-- Output stack (QStackedWidget)
    #         +-- Button grid (QGridLayout)
    #         +-- Reset button (QPushButton)
    #=================================================

    #=================================================
    # initialization
    #=================================================
    def __init__(self):
        super().__init__()
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
    # data preparatiton
    #=================================================
    def _init_data(self):
        self.filtered_authors = []
        self.filtered_books = []
        authors_set = set()

        # filtered books start with full list
        for book in book_collection.The_Collection:
            if book.total_q > 0:
                self.filtered_books.append(book.title)
                authors_set.add(book.author)

        # sorted returns a list
        self.authors_with_quotes = sorted(authors_set)
        self.filtered_authors = self.authors_with_quotes.copy()

    #=================================================
    # default state
    #=================================================
    def _init_state(self):
        self.output_font_size = constants.DEFAULT_OUTPUT_FONT_SIZE
        self.line_height_percent = constants.DEFAULT_LINE_SPACING_HEIGHT
        self.quote_printed = False

        # for delayed author print
        self.author_timer = QTimer(self)
        self.author_timer.setSingleShot(True)
        self.author_timer.timeout.connect(self._print_pending_author)
        self.pending_author_data = None

    #=================================================
    # ComboBox filters (dropdowns)
    #=================================================
    def _init_filters(self):
        self.folders_dropdown = QComboBox()
        self.authors_dropdown = QComboBox()
        self.books_dropdown = QComboBox()
        self.folders_dropdown.addItems([constants.ANY_FOLDER] + sorted(book_collection.Folders.keys()))
        self.authors_dropdown.addItems([constants.ANY_AUTHOR] + self.authors_with_quotes)
        self.books_dropdown.addItems([constants.ANY_BOOK] + self.filtered_books)

        # create searchable dropdowns
        self.authors_dropdown.setEditable(True)
        self.books_dropdown.setEditable(True)

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

        # grab the font of first button (from dictionary list)
        font = self.buttons["random"].font()
        font.setPointSize(font.pointSize() + 1)

        for btn in list(self.buttons.values()) + [
            self.btn_increase, self.btn_decrease, self.delay_author_toggle
        ]:
            btn.setFont(font)
            btn.setMinimumHeight(33)

    #=================================================
    # signals
    #=================================================
    def _init_signals(self):
        # only the function reference is bound here (no call operator "()" added)
        # the folder/author choice event triggers the authors and book lists update
        self.folders_dropdown.currentIndexChanged.connect(self.on_folder_or_author_change)
        self.authors_dropdown.currentIndexChanged.connect(self.on_folder_or_author_change)
        # authors and books are searchable
        self.authors_dropdown.lineEdit().textChanged.connect(self.on_text_changed)
        self.books_dropdown.lineEdit().textChanged.connect(self.on_text_changed)

        self.delay_author_toggle.toggled.connect(self.on_toggle_delay_author)

        # use lambda to defer immediate execution when an argument is passed
        self.buttons["random"].clicked.connect(self.print_random_quote)
        self.buttons["short"].clicked.connect(lambda: self.print_random_quote("short"))
        self.buttons["every"].clicked.connect(self.print_every_quote)
        self.buttons["stats"].clicked.connect(self.print_statistics)
        # self.buttons["dist"].clicked.connect(self.print_quote_distribution)
        self.buttons["dist"].clicked.connect(self.show_quote_distribution_chart)
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

        label_font = QFont("Consolas", 12)

        # addWidget(widget, row, column, rowSpan, columnSpan, alignment)
        dropdown_layout.addWidget(QLabel("FOLDER", font=label_font), 0, 0)
        dropdown_layout.addWidget(self.folders_dropdown, 0, 1)
        dropdown_layout.addWidget(QLabel("AUTHOR", font=label_font), 1, 0)
        dropdown_layout.addWidget(self.authors_dropdown, 1, 1)
        dropdown_layout.addWidget(QLabel("BOOK", font=label_font), 2, 0)
        dropdown_layout.addWidget(self.books_dropdown, 2, 1)
        # labels fixed, dropdowns expand
        dropdown_layout.setColumnStretch(0, 0)
        dropdown_layout.setColumnStretch(1, 1)

        string = f"== The Collection =="
        the_collection_logo = f"{'=' * len(string)}\n{string}\n{'=' * len(string)}"
        logo_text = QLabel(the_collection_logo)
        logo_text.setFont(QFont("Consolas", 14))
        logo_text.setAlignment(Qt.AlignCenter)
        logo_text.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
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
        self.text_output.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.text_output.document().setDocumentMargin(30)

        # column output, set colours
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

        # chart output
        self._quote_chart_widget = QWidget()
        chart_layout = QVBoxLayout(self._quote_chart_widget)
        self._chart_view = QChartView()
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_layout.addWidget(self._chart_view)

        # add widgets to stack
        self.output_stack.addWidget(self.text_output)           # index 0
        self.output_stack.addWidget(self.table_output)          # index 1
        self.output_stack.addWidget(self._quote_chart_widget)   # index 2

        # show text by default
        self.output_stack.setCurrentWidget(self.text_output)

    def show_text_output(self):
        self.output_stack.setCurrentWidget(self.text_output)

    def show_table_output(self):
        self.output_stack.setCurrentWidget(self.table_output)
        self.table_output.resizeColumnsToContents()

    def show_chart_output(self):
        self.output_stack.setCurrentWidget(self._quote_chart_widget)

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
    # FUNCTION: toggle button changer
    #=================================================
    def on_toggle_delay_author(self, checked):
        if not checked and self.pending_author_data:
            self._flush_pending_author()

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
                self.filtered_authors = [constants.ANY_AUTHOR] + self.authors_with_quotes
            else:
                # build list based on current folder (set comprehension)
                folder_authors = {
                    book.author
                    for book in book_collection.The_Collection
                    if book.folder == chosen_folder
                    and book.total_q > 0
                }
                folder_authors = sorted(folder_authors)
                self.filtered_authors = [constants.ANY_AUTHOR] + folder_authors

            self.authors_dropdown.clear()
            self.authors_dropdown.addItems(self.filtered_authors)
            self.authors_dropdown.setCurrentIndex(0)
            chosen_author = constants.ANY_AUTHOR

        # update books based on current folder and author
        self.filtered_books = [constants.ANY_BOOK]
        for book in book_collection.The_Collection:
            if chosen_folder != constants.ANY_FOLDER and book.folder != chosen_folder:
                continue
            if chosen_author != constants.ANY_AUTHOR and book.author != chosen_author:
                continue
            if book.total_q > 0:
                self.filtered_books.append(book.title)

        self.books_dropdown.clear()
        self.books_dropdown.addItems(self.filtered_books)
        self.books_dropdown.setCurrentIndex(0)

    def on_text_changed(self):
        is_author_call = self.sender() == self.authors_dropdown

        target = self.authors_dropdown if is_author_call else self.books_dropdown
        current_items = self.filtered_authors if is_author_call else self.filtered_books

        target.blockSignals(True)
        target.clear()

        line_edit = target.lineEdit().text()
        text = line_edit.lower()

        if not text:
            target.addItems(current_items)
        else:
            for item in current_items:
                if text in item.lower():
                    target.addItem(item)

        target.blockSignals(False)

        # keep the typed text and cursor position
        target.lineEdit().setText(line_edit)
        target.lineEdit().setCursorPosition(len(line_edit))

        # optionally show the dropdown automatically
        target.showPopup()

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
    def log(self, message):
        # make sure text output is visible
        self.show_text_output()
        self.text_output.append(message)
        self.set_output_line_height(self.line_height_percent)

    def set_output_line_height(self, line_height_percent):
        cursor = self.text_output.textCursor()
        cursor.beginEditBlock()

        # iterate over all blocks in the document
        block = self.text_output.document().firstBlock()
        while block.isValid():
            # select block
            cursor.setPosition(block.position())
            cursor.setPosition(block.position() + block.length() - 1, QTextCursor.KeepAnchor)

            # apply formatting
            block_fmt = QTextBlockFormat()
            block_fmt.setLineHeight(line_height_percent, QTextBlockFormat.ProportionalHeight.value)
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

    def _build_headers(self, book_property):
        headers = [
            "" if book_property != constants.PROP_READ_DURATION else "Read duration",
            "" if book_property != constants.PROP_READ_DURATION else "Pages / day",
            "Author",
            "Title",
            "Year",
            "Rating",
            "Ratings x1000",
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
            book_collection.The_Collection
            if folder == constants.ANY_FOLDER
            else [b for b in book_collection.The_Collection if b.folder == folder]
        )
        # further filter books based on selected property
        if book_property == constants.PROP_READING_NOW:
            return [b for b in books if b.activity_time and not b.is_read]

        if book_property in (constants.PROP_READ_DURATION, constants.PROP_FINISHED_LIST):
            return [b for b in books if b.is_read]

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
            int(book.total_q),
            int(book.pages_count),
            book.q_per_page,
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

    def _get_read_duration_data(self, book):
        if (book.first_q_timestamp <= constants.START_DATE_FOR_READ_LIST or
            (book.last_q_timestamp - book.first_q_timestamp) <= constants.ONE_DAY_IN_SECONDS or
            book.title in constants.EXCLUDED_TITLES_FROM_READ_DURATION):
            return "", 0

        # compute elapsed days if needed
        dt_first = datetime.datetime.fromtimestamp(book.first_q_timestamp)
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
            self.quote_printed = False
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
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # flush any pending author data without print
        self._flush_pending_author(print_data=False)

        # rebuild collection and reset dropdowns
        book_collection.build_the_collection()
        self.folders_dropdown.setCurrentIndex(0)
        self.authors_dropdown.setCurrentIndex(0)
        self.books_dropdown.setCurrentIndex(0)
        # build full dropdown lists again
        self.on_folder_or_author_change()

        # reset UI state
        self.delay_author_toggle.setChecked(False)
        self.quote_printed = False
        self.clear()

        # reset font and layout settings
        self.output_font_size = constants.DEFAULT_OUTPUT_FONT_SIZE
        self.line_height_percent = constants.DEFAULT_LINE_SPACING_HEIGHT
        self.text_output.setFont(QFont("Consolas", self.output_font_size))

        # reset mode dropdown
        self.mode_dropdown.setCurrentIndex(0)
        self.update_mode_dropdown_text()

    #=================================================
    # BUTTON FUNCTIONS
    #=================================================
    #=================================================
    # FUNCTION: print random quote
    #=================================================
    def print_random_quote(self, length="any"):
        # print any remaining author data
        self._flush_pending_author()

        selected_title = self.books_dropdown.currentText()
        delay_author = self.delay_author_toggle.isChecked()

        book, message = book_utils.get_book_for_random_quote(
            book_collection.The_Collection,
            selected_title,
            self.filtered_books,
            length
        )

        # add space before previous print (but not before the first)
        if self.quote_printed:
            self.log("\n")
        self.quote_printed = True

        if book is None:
            self.log(message)
            return

        # get the random quote and print it
        random_quote, quotes_left = book_utils.get_random_quote(book, length)
        self.log(random_quote.text)
        # ensure the last line is visible
        self.scroll_to_bottom()

        if not delay_author:
            self._print_author_now(book, quotes_left)
        else:
            self._schedule_author(book, quotes_left, len(random_quote.text))

    def scroll_to_bottom(self):
        cursor = self.text_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_output.setTextCursor(cursor)
        self.text_output.ensureCursorVisible()

    def _print_author_now(self, book, quotes_left):
        self.log(f"\n{book.title}   / {quotes_left} left /")
        self.log(f"{'-'*len(book.title)}")
        # ensure the last line is visible
        self.scroll_to_bottom()

    def _schedule_author(self, book, quotes_left, quote_length, base_delay_ms=1000, ms_per_char=50):
        delay_ms = min(base_delay_ms + quote_length * ms_per_char, 60000)
        self.pending_author_data = (book, quotes_left)

        # stop previous timer if running
        if self.author_timer.isActive():
            self.author_timer.stop()

        # start the timer
        self.author_timer.start(delay_ms)

    def _print_pending_author(self):
        if self.pending_author_data:
            # unpack the stored tuple
            book, quotes_left = self.pending_author_data
            self._print_author_now(book, quotes_left)
        self.pending_author_data = None

    def _flush_pending_author(self, print_data=True):
        if self.author_timer.isActive():
            self.author_timer.stop()
        if print_data and self.pending_author_data:
            book, quotes_left = self.pending_author_data
            self._print_author_now(book, quotes_left)
        self.pending_author_data = None

    #=================================================
    # FUNCTION: print every quote
    #=================================================
    def print_every_quote(self):
        self.clear()

        selected_title = self.books_dropdown.currentText()
        if selected_title == constants.ANY_BOOK:
            self.log("Select a book from the list.")
            return

        book = book_utils.get_book_by_title(book_collection.The_Collection, selected_title)
        if book is None:
            self.log("Book not found.")
            return

		# get and export all quotes to file
        quotes = book_utils.get_and_export_quotes(book, f"{book.title}.txt")

		# print to textbox
        self.log(book.title)
        self.log('-' * len(book.title))

        for i, quote in enumerate(quotes):
            header = f"{i+1} / {len(quotes)}  (p.{quote.page})"
            self.log(header)
            self.log(quote.text)
            self.log("")

    #=================================================
    # FUNCTION: print quote distribution
    #=================================================
    def print_quote_distribution(self):
        self.clear()

        # get the book
        selected_title = self.books_dropdown.currentText()
        if selected_title == constants.ANY_BOOK:
            self.log("Select a book from the list.")
            return

        book = book_utils.get_book_by_title(book_collection.The_Collection, selected_title)
        title = book.title
        self.log(title)
        self.log("-" * len(title))
        self.log("")

        font_metrics = self.text_output.fontMetrics()
        avg_char_width = font_metrics.horizontalAdvance("X")
        # margin was added to the text output
        ctrl_width_px = self.text_output.width()-30
        columns = book_utils.calculate_columns_from_width(ctrl_width_px, avg_char_width)
        rows = round(columns * 0.2)
        space = "  "
        # get distribution using utils
        mapped_distr = book_utils.compute_quote_distribution(book, columns=columns, rows=rows)
        # draw diagram
        self.log(f"{space}↑")
        for i in range(rows):
            row = ''.join('*' if mapped_distr[j] >= (rows-i) else ' ' for j in range(columns))
            self.log(f"{space}|{row}")
        self.log(f"{space}{'-'*columns}→")
        self.log(f"{space}1{' '*(columns-len(str(book.pages_count))+1)}{book.pages_count}")
        self.log("")

    def show_quote_distribution_chart(self):
        # get the book
        selected_title = self.books_dropdown.currentText()
        if selected_title == constants.ANY_BOOK:
            self.log("Select a book from the list.")
            return

        book = book_utils.get_book_by_title(book_collection.The_Collection, selected_title)

        # proportional columns: e.g., 1 bar per 5 pages, min 10 bars, max 100 bars
        columns = max(10, min(book.pages_count // 5, 100))
        mapped_distr = book_utils.compute_quote_distribution_for_chart(book, columns=columns)

        # build chart
        bar_set = QBarSet("Quote Length")
        bar_set.append(mapped_distr)
        series = QBarSeries()
        series.append(bar_set)

        # create chart and add series
        chart = QChart()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setTitle(f"Quote Distribution: {book.title}")

        # set Y-axis scale dynamically based on data
        axisY = QValueAxis()
        axisY.setRange(0, max(mapped_distr)*1.1)  # 10% headroom
        chart.setAxisY(axisY, series)

        # show values on top of bars
        bar_set.setLabelVisible(True)
        bar_set.setLabelsAngle(-90)

        # update the existing chart view
        self._chart_view.setChart(chart)
        self.show_chart_output()

    #=================================================
    # FUNCTION: print statistics
    #=================================================
    def print_statistics(self):
        self.clear()
        author_quotes = {}
        folder_q_count = {}
        folder_book_count = {}

        # gather book counts
        books_with_quotes, books_20th, books_21st, books_read_count = 0, 0, 0, 0
        for book in book_collection.The_Collection:
            if book.total_q > 0:
                books_with_quotes += 1
            if 1900 <= book.published_date < 2000:
                books_20th += 1
            if book.published_date >= 2000:
                books_21st += 1
            if book.is_read:
                books_read_count += 1

            # gather folders statistics
            for folder in book_collection.Folders:
                if book.folder == folder:
                    folder_q_count[folder] = folder_q_count.get(folder, 0) + book.total_q
                    folder_book_count[folder] = folder_book_count.get(folder, 0) + 1
                    break

            if book.total_q > 0:
                author_quotes[book.author] = author_quotes.get(book.author, 0) + book.total_q

        #=================================================
        # books
        #=================================================
        string = "Statistics"
        self.log(f"{string}\n{'-'*len(string)}\n")
        books_count = len(book_collection.The_Collection)
        self.print_stat_line("Books in The Collection", f"{books_count:4d} / 100%")
        if books_21st:
            self.print_stat_line("Books from the 21st century", f"{books_21st:4d} / {self.get_percentage_string(books_21st, books_count)}")
        if books_20th:
            self.print_stat_line("Books from the 20th century", f"{books_20th:4d} / {self.get_percentage_string(books_20th, books_count)}")
        self.print_stat_line("Books with quotes", f"{books_with_quotes:4d} / {self.get_percentage_string(books_with_quotes, books_count)}")
        self.print_stat_line("Books finished", f"{books_read_count:4d} / {self.get_percentage_string(books_read_count, books_count)}", blank_line=True)

        # Sort folders by book count (descending)
        folder_book_count = dict(sorted(folder_book_count.items(), key=lambda item: item[1], reverse=True))
        self.print_folder_dict(folder_book_count, books_count)

        #=================================================
        # quotes
        #=================================================
        self.print_stat_line("Quotes in total", f"{book_collection.All_Quotes_Count:4d} / 100%")
        string = f"{book_collection.Short_Quotes_Count:4d} / {self.get_percentage_string(book_collection.Short_Quotes_Count, book_collection.All_Quotes_Count)}"
        self.print_stat_line(f"Quotes that are less than {constants.MAX_CHAR_IN_SHORT_QUOTE} characters", string)
        self.print_stat_line("Quotes per book on average", f"{round(book_collection.All_Quotes_Count / books_with_quotes):4d}", blank_line=True)

        folder_q_count = dict(sorted(folder_q_count.items(), key=lambda item: item[1], reverse=True))
        self.print_folder_dict(folder_q_count, book_collection.All_Quotes_Count)

        #=================================================
        # authors
        #=================================================
        string = "Top 15 Authors"
        self.log(f"{string}\n{'-'*len(string)}")

        # sort authors by total quotes (descending)
        author_quotes = dict(sorted(author_quotes.items(), key=lambda item: item[1], reverse=True))
        cumulative = 0
        for i, (author, count) in enumerate(author_quotes.items(), start=1):
            cumulative += count
            self.print_stat_line(
                f" --> {author}",
                f"{count:4d} / {self.get_percentage_string(count, book_collection.All_Quotes_Count, digit=2)}"
                f" / {self.get_percentage_string(cumulative, book_collection.All_Quotes_Count, digit=2)}"
            )
            if i >= 15:
                break

        #=================================================
        # words
        #=================================================
        string = "Top 30 most used words"
        self.log(f"\n\n{string}\n{'-'*len(string)}")

        all_quotes_list = []
        for book in book_collection.The_Collection:
            all_quotes_list += book.get_all_quotes_list()
        all_text = ' '.join(quote.text for quote in all_quotes_list)

        pattern = r"\b(?:" + '|'.join(constants.WORDS_TO_OMIT_FROM_SEARCH) + r")\b"
        updated_text = re.sub(pattern, "", all_text, flags=re.IGNORECASE)

        # convert to lowercase and split by non-word characters (e.g., punctuation)
        words = re.findall(r"\b\w{4,}\b", updated_text.lower())
        top_30 = Counter(words).most_common(30)

        # get word counts for each book, omitted words from top_30 will be
        # also counted, but there will be no match during later check
        book_word_counts = {}
        for book in book_collection.The_Collection:
            quotes_text = ' '.join(quote.text for quote in book.get_all_quotes_list()).lower()
            word_counts = Counter(re.findall(r'\b\w{4,}\b', quotes_text))
            book_word_counts[book.title] = word_counts

        # process the top 30 words
        for word, count in top_30:
            # find the book with the most occurrence of the word
            max_count = 0
            book_string = ""
            for book in book_collection.The_Collection:
                word_count = book_word_counts[book.title].get(word, 0)
                if word_count > max_count:
                    max_count = word_count
                    book_string = book.title
            # print related data in one line
            self.log(f" --> {count:3d} x {word}{' '*(12-len(word))}{max_count:3d} / {book_string}")

    def print_stat_line(self, string, value, blank_line=False):
        self.log(f"{string}  {'-'*(48-len(string))}>  {value}")
        if blank_line:
            self.log("")

    def get_percentage_string(self, count, total, digit=3):
        return f"{int((count/total)*100):{digit}d}%" if total else "0%"

    def print_folder_dict(self, folder_dict, total):
        cumulative = 0
        for folder in folder_dict:
            cumulative += folder_dict[folder]
            self.print_stat_line(
                f" --> {folder}",
                f"{folder_dict[folder]:4d} / {self.get_percentage_string(folder_dict[folder], total)}"
            )
        self.log("\n")

    #=================================================
    # FUNCTION: search in quotes
    #=================================================
    def search(self):
        # create normal/match text formats
        fmt_normal = QTextCharFormat()
        fmt_normal.setFontWeight(QFont.Normal)
        fmt_normal.clearBackground()

        fmt_match = QTextCharFormat()
        # fmt_match.setFontItalic(True)
        fmt_match.setFontWeight(QFont.Bold)

        # popup for user input
        text, ok = QInputDialog.getText(self, "Search", "Enter at least 3 characters:")
        if not ok:
            # user cancelled
            return
        else:
            self.clear()

        # check length
        str_to_search = text.strip().lower()
        if len(str_to_search) < 3:
            self.log("Incorrect input. Please enter at least 3 characters.\n")
            return

        selected_title = self.books_dropdown.currentText()
        if selected_title == constants.ANY_BOOK:
            books = [book for book in book_collection.The_Collection if book.title in self.filtered_books]
        else:
            book = book_utils.get_book_by_title(book_collection.The_Collection, selected_title)
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
        cursor.movePosition(QTextCursor.End)

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
    import sys
    error = book_collection.build_the_collection()
    app = QApplication(sys.argv)
    window = MainWindow()
    if error:
        window.log(f"Error reading JSON file: {error}")
    sys.exit(app.exec())
