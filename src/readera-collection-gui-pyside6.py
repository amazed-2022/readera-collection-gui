#=================================================
# IMPORT
#=================================================
import book_collection
import book_utils
from constants_loader import constants
import datetime
import random
import re
import textwrap
from collections import Counter

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QTextOption
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QComboBox,
    QMessageBox, QInputDialog
)

#=================================================
# MAIN WINDOW
#=================================================
class MainWindow(QMainWindow):

    #=================================================
    # initialization
    #=================================================
    def __init__(self):
        super().__init__()
        self.setWindowTitle(constants.GUI_TITLE)
        self.resize(*constants.WINDOW_SIZE)

        panel = QWidget()
        self.setCentralWidget(panel)
        
        #=================================================
        # data preparation
        #=================================================
        self.filtered_books = []
        authors_set = set()
        
        # filtered books start with full list
        for book in book_collection.The_Collection:
            if book.total_q > 0:
                self.filtered_books.append(book.title)
                authors_set.add(book.author)
                
        # sorted returns a list
        self.authors_with_quotes = sorted(authors_set)
        
        # for delayed author print
        self.author_timer = None
        self.pending_author_data = None
        
        #=================================================
        # dropdowns
        #=================================================
        # create ComboBox objects (dropdowns)
        self.folders_dropdown = QComboBox()
        self.authors_dropdown = QComboBox()
        self.books_dropdown = QComboBox()
        self.folders_dropdown.addItems([constants.ANY_FOLDER] + sorted(list(book_collection.Folders.keys())))
        self.authors_dropdown.addItems([constants.ANY_AUTHOR] + self.authors_with_quotes)
        self.books_dropdown.addItems([constants.ANY_BOOK] + self.filtered_books)
        self.folders_dropdown.setCurrentIndex(0)
        self.authors_dropdown.setCurrentIndex(0)
        self.books_dropdown.setCurrentIndex(0)
        
        # only the function reference is bound here
        # the folder/author choice event triggers the authors and book lists update
        self.folders_dropdown.currentIndexChanged.connect(self.on_folder_or_author_change)
        self.authors_dropdown.currentIndexChanged.connect(self.on_folder_or_author_change)
        
        # increase font size for dropdowns
        font = self.folders_dropdown.font()
        font.setPointSize(font.pointSize() + 1)
        self.folders_dropdown.setFont(font)
        self.authors_dropdown.setFont(font)
        self.books_dropdown.setFont(font)
        
        # create the dropdown grid layout
        dropdown_layout = QGridLayout()
        dropdown_layout.addWidget(QLabel("FOLDER"), 0, 0)
        dropdown_layout.addWidget(self.folders_dropdown, 0, 1)
        dropdown_layout.addWidget(QLabel("AUTHOR"), 1, 0)
        dropdown_layout.addWidget(self.authors_dropdown, 1, 1)
        dropdown_layout.addWidget(QLabel("BOOK"), 2, 0)
        dropdown_layout.addWidget(self.books_dropdown, 2, 1)
        
        #=================================================
        # logo and text layout
        #=================================================
        string = f"== The Collection =="
        separator = '=' * len(string)
        the_collection_logo = f"{separator}\n{string}\n{separator}"
        logo_text = QLabel(the_collection_logo)
        logo_text.setFont(QFont("Monospace", 14))
        logo_text.setAlignment(Qt.AlignCenter)
        
        text_layout = QHBoxLayout()
        text_layout.addStretch(1)
        text_layout.addWidget(logo_text)
        text_layout.addStretch(1)
        
        #=================================================
        # finish header layout
        #=================================================
        header_layout = QHBoxLayout()
        header_layout.addLayout(dropdown_layout, 1)
        header_layout.addLayout(text_layout, 0)
        
        #========================
        # HORIZONTAL output layout
        #========================
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Monospace", 13))
        self.output.setStyleSheet("background-color: rgb(240,230,200);")
        self.output.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        
        #=============
        # grid_layout
        #=============
        self.delay_author_toggle = QPushButton("Random quotes: delay author")
        self.delay_author_toggle.setCheckable(True)
        self.delay_author_toggle.setChecked(False)
        self.delay_author_toggle.setToolTip("ON: Author appears after a delay\nOFF: Author appears immediately")
        self.delay_author_toggle.toggled.connect(self.on_toggle_delay_author)
        
        btn1 = QPushButton("Random quote")
        btn1.clicked.connect(lambda: self.print_random_quote())
        btn2 = QPushButton("Print every quote")
        btn2.clicked.connect(self.print_every_quote)
        btn3 = QPushButton("Statistics")
        btn3.clicked.connect(self.print_statistics)
        btn4 = QPushButton("Random short quote")
        btn4.clicked.connect(lambda: self.print_random_quote("short"))
        btn5 = QPushButton("Quote distribution")
        btn5.clicked.connect(self.print_quote_distribution)
        btn6 = QPushButton("Search")
        btn6.clicked.connect(self.search)
        btn7 = QPushButton("Clear window")
        btn7.clicked.connect(self.clear)
        btn8 = QPushButton("Book list by property")
        btn8.clicked.connect(self.print_list_by_property)
        
        font_btn = btn1.font()
        font_btn.setPointSize(font_btn.pointSize() + 1)
        for b in [btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, self.delay_author_toggle]:
            b.setFont(font_btn)
            b.setMinimumHeight(33)
        
        grid_layout = QGridLayout()
        grid_buttons = [
            btn1, btn2, btn3,
            btn4, btn5, btn6,
            self.delay_author_toggle, btn7, btn8
        ]
        
        positions = [(i,j) for i in range(3) for j in range(3)]
        for pos, btn in zip(positions, grid_buttons):
            grid_layout.addWidget(btn, pos[0], pos[1])
        
        #=============
        # reset_layout
        #=============
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset)
        reset_button.setToolTip("Reset all settings and clear the output")
        reset_button.setFont(font_btn)
        reset_button.setMinimumHeight(36)
        reset_button.setStyleSheet("background-color: rgb(220,220,220);")
        
        #==================================
        # full window (VERTICAL main_layout)
        #==================================
        main_layout = QVBoxLayout()
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.output, 1)
        main_layout.addLayout(grid_layout)
        main_layout.addWidget(reset_button)
        panel.setLayout(main_layout)
        
        self.show()

    #=================================================
    # FUNCTION: toggle button changer
    #=================================================
    def on_toggle_delay_author(self, checked):
        if checked:
            self.delay_author_toggle.setStyleSheet("background-color: rgb(180,230,180);")
        else:
            self.delay_author_toggle.setStyleSheet("")
            if self.pending_author_data:
                self._flush_pending_author()

    #=================================================
    # FUNCTION: folder/author dropdown change
    #=================================================
    def on_folder_or_author_change(self):
        # gets the widget that triggered the signal
        sender = self.sender()  
        chosen_folder = self.folders_dropdown.currentText()
        chosen_author = self.authors_dropdown.currentText()

        # update authors dropdown if folder changed and reset chosen author
        if sender == self.folders_dropdown:
            if chosen_folder == constants.ANY_FOLDER:
                authors = [constants.ANY_AUTHOR] + self.authors_with_quotes
            else:
                folder_authors = {
                    book.author
                    for book in book_collection.The_Collection
                    if book.folder == chosen_folder
                    and book.total_q > 0
                }
                folder_authors = sorted(folder_authors)
                authors = [constants.ANY_AUTHOR] + folder_authors
                
            self.authors_dropdown.clear()
            self.authors_dropdown.addItems(authors)
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

    #=================================================
    # FUNCTION: log messages to the text box
    #=================================================
    def log(self, message):
        self.output.append(message)

    #=================================================
    # FUNCTION: clear
    #=================================================
    def clear(self):
        self.output.clear()

    #=================================================
    # FUNCTION: reset
    #=================================================
    def reset(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Confirm Reset")
        dlg.setText("Are you sure you want to reset everything?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Warning)
        if dlg.exec() == QMessageBox.Yes:
            self._flush_pending_author(print_data=False)
            book_collection.build_the_collection()
            self.folders_dropdown.setCurrentIndex(0)
            self.authors_dropdown.setCurrentIndex(0)
            self.books_dropdown.setCurrentIndex(0)
            self.on_folder_or_author_change()
            self.delay_author_toggle.setChecked(False)
            self.clear()

    #=================================================
    # FUNCTION: print wrapped text
    #=================================================
    def print_wrapped_text(self, text, min_width=20, padding=20):
        font_metrics = self.output.fontMetrics()
        avg_char_width = font_metrics.horizontalAdvance("X")
        text_ctrl_width = self.output.width() - padding
        wrap_width_chars = max(min_width, int(text_ctrl_width / avg_char_width) - 1)
        wrapped_text = textwrap.fill(text, width=wrap_width_chars)
        self.log(wrapped_text)

    #=================================================
    # BUTTON FUNCTIONS
    #=================================================
    #=================================================
    # FUNCTION: print random quote
    #=================================================
    def print_random_quote(self, length="any"):
        self._flush_pending_author()
        
        selected_title = self.books_dropdown.currentText()
        delay_author = self.delay_author_toggle.isChecked()

        book, message = book_utils.get_book_for_random_quote(
            book_collection.The_Collection,
            selected_title,
            self.filtered_books,
            length
        )

        if book is None:
            self.log(message)
            return

        random_quote, quotes_left = book_utils.get_random_quote(book, length)

        self.print_wrapped_text(random_quote.text)

        if not delay_author:
            self._print_author_now(book, quotes_left)
        else:
            self._schedule_author(book, quotes_left, len(random_quote.text))

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

        quotes = book_utils.get_and_export_quotes(book, f"{book.title}.txt")

        self.log(book.title)
        self.log('-' * len(book.title))

        for i, quote in enumerate(quotes):
            header = f"{i+1} / {len(quotes)}  (p.{quote.page})"
            self.log(header)
            self.print_wrapped_text(quote.text)
            self.log("")

    #=================================================
    # FUNCTION: print quote distribution
    #=================================================
    def print_quote_distribution(self):
        self.clear()
        selected_title = self.books_dropdown.currentText()
        if selected_title == constants.ANY_BOOK:
            self.log("Select a book from the list.")
            return

        book = book_utils.get_book_by_title(book_collection.The_Collection, selected_title)
        title = book.title
        self.log(title)
        self.log("-" * len(title))
        self.log("")

        font_metrics = self.output.fontMetrics()
        avg_char_width = font_metrics.horizontalAdvance("X")
        ctrl_width_px = self.output.width()
        columns = book_utils.calculate_columns_from_width(ctrl_width_px, avg_char_width)
        rows = round(columns * 0.2)
        space = "   "

        mapped_distr = book_utils.compute_quote_distribution(book, columns=columns, rows=rows)

        self.log(f"{space}↑")
        for i in range(rows):
            row = ''.join('*' if mapped_distr[j] >= (rows-i) else ' ' for j in range(columns))
            self.log(f"{space}|{row}")
        self.log(f"{space}{'-'*columns}→")
        self.log(f"{space}1{' '*(columns-len(str(book.pages_count))+1)}{book.pages_count}")
        self.log("")

    #=================================================
    # FUNCTION: print books list by property
    #=================================================
    def print_list_by_property(self):
        self.clear()
        items, ok = QInputDialog.getItem(self, "Book Properties", "Select a property to sort/filter books by:", constants.PROPERTIES, 0, False)
        if not ok:
            return
        book_property = items
        sorted_books = book_utils.sort_books_for_property(book_collection.The_Collection, book_property)
        folder = self.folders_dropdown.currentText()
        filtered_books = book_utils.filter_books_by_folder(sorted_books, folder)

        for book in filtered_books:
            line = book_utils.get_info_row_by_property(book, book_property, print_pages=(book_property == constants.PROP_PUBLISH_DATE))
            if line:
                self.log(f"  -->  {line}")

        if book_property == constants.PROP_RATING:
            sorted_books = book_utils.sort_books_for_property(book_collection.The_Collection, constants.PROP_RATINGS_COUNT)
            filtered_books = book_utils.filter_books_by_folder(sorted_books, folder)
            self.log("\n")
            for book in filtered_books:
                line = book_utils.get_info_row_by_property(book, constants.PROP_RATINGS_COUNT)
                if line:
                    self.log(f"  -->  {line}")
        elif book_property == constants.PROP_FINISHED_LIST:
            sorted_books = book_utils.sort_books_for_property(book_collection.The_Collection, constants.PROP_PUBLISH_DATE)
            filtered_books = book_utils.filter_books_by_folder(sorted_books, folder)
            self.log("\n")
            for book in filtered_books:
                line = book_utils.get_info_row_by_property(book, constants.PROP_PUBLISH_DATE, require_finished=True)
                if line:
                    self.log(f"  -->  {line}")

    #=================================================
    # FUNCTION: print statistics
    #=================================================
    def print_statistics(self):
        self.clear()
        author_quotes = {}
        folder_q_count = {}
        folder_book_count = {}

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

            for folder in book_collection.Folders:
                if book.folder == folder:
                    folder_q_count[folder] = folder_q_count.get(folder, 0) + book.total_q
                    folder_book_count[folder] = folder_book_count.get(folder, 0) + 1
                    break

            if book.total_q > 0:
                author_quotes[book.author] = author_quotes.get(book.author, 0) + book.total_q

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

        folder_book_count = dict(sorted(folder_book_count.items(), key=lambda item: item[1], reverse=True))
        self.print_folder_dict(folder_book_count, books_count)

        self.print_stat_line("Quotes in total", f"{book_collection.All_Quotes_Count:4d} / 100%")
        string = f"{book_collection.Short_Quotes_Count:4d} / {self.get_percentage_string(book_collection.Short_Quotes_Count, book_collection.All_Quotes_Count)}"
        self.print_stat_line(f"Quotes that are less than {constants.MAX_CHAR_IN_SHORT_QUOTE} characters", string)
        self.print_stat_line("Quotes per book on average", f"{round(book_collection.All_Quotes_Count / books_with_quotes):4d}", blank_line=True)

        unprinted_quotes = sum(book.total_q - len(book.selected_set) for book in book_collection.The_Collection)
        self.log(unprinted_quotes)

        folder_q_count = dict(sorted(folder_q_count.items(), key=lambda item: item[1], reverse=True))
        self.print_folder_dict(folder_q_count, book_collection.All_Quotes_Count)

        self.log("")
        string = "Top 15 Authors"
        self.log(f"{string}\n{'-'*len(string)}")
        author_quotes = dict(sorted(author_quotes.items(), key=lambda item: item[1], reverse=True))
        cumulative = 0
        for i, (author, count) in enumerate(author_quotes.items(), start=1):
            cumulative += count
            self.print_stat_line(f" --> {author}", f"{count:4d} / {self.get_percentage_string(count, book_collection.All_Quotes_Count, digit=2)} / {self.get_percentage_string(cumulative, book_collection.All_Quotes_Count, digit=2)}")
            if i >= 15:
                break

        self.log("\n")
        string = "Top 30 most used words"
        self.log(f"\n{string}\n{'-'*len(string)}")

        all_quotes_list = []
        for book in book_collection.The_Collection:
            all_quotes_list += book.get_all_quotes_list()
        all_text = ' '.join(quote.text for quote in all_quotes_list)

        pattern = r"\b(?:" + '|'.join(constants.WORDS_TO_OMIT_FROM_SEARCH) + r")\b"
        updated_text = re.sub(pattern, "", all_text, flags=re.IGNORECASE)

        words = re.findall(r"\b\w{4,}\b", updated_text.lower())
        top_30 = Counter(words).most_common(30)

        book_word_counts = {}
        for book in book_collection.The_Collection:
            quotes_text = ' '.join(quote.text for quote in book.get_all_quotes_list()).lower()
            word_counts = Counter(re.findall(r'\b\w{4,}\b', quotes_text))
            book_word_counts[book.title] = word_counts

        for word, count in top_30:
            max_count = 0
            book_string = ""
            for book in book_collection.The_Collection:
                word_count = book_word_counts[book.title].get(word, 0)
                if word_count > max_count:
                    max_count = word_count
                    book_string = book.title
            self.log(f" --> {count:3d} x {word}{' '*(12-len(word))}{max_count:3d} / {book_string}")

    #=================================================
    # HELPER FUNCTIONS
    #=================================================
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
            self.print_stat_line(f" --> {folder}", f"{folder_dict[folder]:4d} / {self.get_percentage_string(folder_dict[folder], total)}")
        self.log("\n")

    #=================================================
    # FUNCTION: search in quotes
    #=================================================
    def search(self):
        self.clear()
        text, ok = QInputDialog.getText(self, "Search", "Enter at least 3 characters:")
        if not ok:
            return
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
                    highlighted_text = self.highlight(quote.text, str_to_search)
                    self.print_wrapped_text(highlighted_text)
                    self.log('\n')
                    counter += len(re.findall(str_to_search, quote_text))

        result = f"Matched {counter} time{'s' if counter != 1 else ''}."
        self.log(result if counter else "No match found.")
        if counter:
            self.log('-'*len(result))
        self.log('\n')

    def highlight(self, text, term):
        return re.sub(re.escape(term), lambda m: m.group(0).upper(), text, flags=re.IGNORECASE)

    #=================================================
    # AUTHOR DELAY HELPERS
    #=================================================
    def _print_author_now(self, book, quotes_left):
        self.log(f"\n{book.title}   / {quotes_left} left /")
        self.log(f"{'-'*len(book.title)}\n\n")

    def _schedule_author(self, book, quotes_left, quote_length, base_delay_ms=1000, ms_per_char=50):
        delay_ms = min(base_delay_ms + quote_length * ms_per_char, 60000)
        self.pending_author_data = (book, quotes_left)
        self.author_timer = QTimer.singleShot(delay_ms, self._print_pending_author)

    def _print_pending_author(self):
        if self.pending_author_data:
            book, quotes_left = self.pending_author_data
            self._print_author_now(book, quotes_left)
        self.pending_author_data = None
        self.author_timer = None

    def _flush_pending_author(self, print_data=True):
        if self.author_timer:
            self.author_timer = None
        if print_data and self.pending_author_data:
            book, quotes_left = self.pending_author_data
            self._print_author_now(book, quotes_left)
        self.pending_author_data = None

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
