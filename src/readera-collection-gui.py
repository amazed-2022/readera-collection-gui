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
import wx
from collections import Counter

#=================================================
# MAIN FRAME
#=================================================
class MainFrame(wx.Frame):

    #=================================================
    # initialization
    #=================================================
    def __init__(self):
        super().__init__(None, title=constants.GUI_TITLE, size=constants.WINDOW_SIZE)
        panel = wx.Panel(self)

        #=============
        # full window
        # +-------------------------------------------------+
        # | header_sizer (dropdowns left, logo right)       |
        # +-------------------------------------------------+
        # | output_sizer (text output, expands vertically)  |
        # +-------------------------------------------------+
        # | grid_sizer (3x3 buttons)                        |
        # +-------------------------------------------------+
        # | reset_sizer (full-width reset button)           |
        # +-------------------------------------------------+

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

        #=========================
        # HORIZONTAL header_sizer
        # +----------------------------------------------------------------------------------------------+
        # | dropdown_sizer (FlexGridSizer 3x2)   |      text_sizer                                       |
        # +----------------------------------------------------------------------------------------------+
        # |  FOLDER      [folders]               |  left       |   ====================    |  right      |
        # |  AUTHOR      [authors]               |  expanding  |   == The Collection ==    |  expanding  |
        # |  BOOK        [books]                 |  space      |   ====================    |  space      |
        # +----------------------------------------------------------------------------------------------+

        #=================================================
        # dropdowns
        #=================================================
        # create "Choice" objects (dropdowns)
        self.folders_dropdown = wx.Choice(panel, choices=[constants.ANY_FOLDER] + sorted(list(book_collection.Folders.keys())))
        self.authors_dropdown = wx.Choice(panel, choices=[constants.ANY_AUTHOR] + self.authors_with_quotes)
        self.books_dropdown = wx.Choice(panel, choices=[constants.ANY_BOOK] + self.filtered_books)
        self.folders_dropdown.SetSelection(0)
        self.authors_dropdown.SetSelection(0)
        self.books_dropdown.SetSelection(0)

        # only the function reference is bound here
        # the folder/author choice event triggers the authors and book lists update
        self.folders_dropdown.Bind(wx.EVT_CHOICE, self.on_folder_or_author_change)
        self.authors_dropdown.Bind(wx.EVT_CHOICE, self.on_folder_or_author_change)

        # increase font size for dropdowns
        font = self.folders_dropdown.GetFont()
        font.SetPointSize(font.GetPointSize() + 1)
        self.folders_dropdown.SetFont(font)
        self.authors_dropdown.SetFont(font)
        self.books_dropdown.SetFont(font)

        # create the dropdown grid sizer
        dropdown_sizer = wx.FlexGridSizer(rows=3, cols=2, vgap=8, hgap=8)
        dropdown_sizer.AddGrowableCol(1, 1)
        dropdown_sizer.Add(wx.StaticText(panel, label="FOLDER"), proportion=0, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT, border=30)
        dropdown_sizer.Add(self.folders_dropdown, proportion=1, flag=wx.EXPAND)
        dropdown_sizer.Add(wx.StaticText(panel, label="AUTHOR"), proportion=0, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT, border=30)
        dropdown_sizer.Add(self.authors_dropdown, proportion=1, flag=wx.EXPAND)
        dropdown_sizer.Add(wx.StaticText(panel, label="BOOK"), proportion=0, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT, border=30)
        dropdown_sizer.Add(self.books_dropdown, proportion=1, flag=wx.EXPAND)

        #=================================================
        # create header sizer
        #=================================================
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        header_sizer.Add(dropdown_sizer, 1, wx.EXPAND)

        #=================================================
        # logo and text sizer
        #=================================================
        string = f"== The Collection =="
        separator = '=' * len(string)
        the_collection_logo = f"{separator}\n{string}\n{separator}"
        logo_text = wx.StaticText(panel, label=the_collection_logo)
        logo_text.SetFont(wx.Font(14, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        text_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # stretch spacer is basically an expanding empty item (proportion=1)
        text_sizer.AddStretchSpacer(1)
        text_sizer.Add(logo_text, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL)
        text_sizer.AddStretchSpacer(1)
        text_sizer.SetMinSize((500, -1))

        #=================================================
        # finish header sizer
        #=================================================
        header_sizer.Add(text_sizer, 0, wx.EXPAND)

        #========================
        # HORIZONTAL output_sizer
        # +--------------------------------------+
        # |  +--------------------------------+  |
        # |  | output_pad (Panel)             |  |
        # |  |                                |  |
        # |  |  inner_sizer (VERTICAL)        |  |
        # |  |   +------------------------+   |  |
        # |  |   | self.output (TextCtrl) |   |  |
        # |  |   |                        |   |  |
        # |  |   |                        |   |  |
        # |  |   |                        |   |  |
        # |  |   |                        |   |  |
        # |  |   +------------------------+   |  |
        # |  +--------------------------------+  |
        # +--------------------------------------+
        output_pad = wx.Panel(panel)
        output_pad.SetBackgroundColour(wx.Colour(240, 230, 200))

        self.output = wx.TextCtrl(output_pad, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.NO_BORDER)
        self.output.SetFont(wx.Font(13, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.output.SetBackgroundColour(wx.Colour(240, 230, 200))
        self.output.SetForegroundColour(wx.BLACK)

        inner_sizer = wx.BoxSizer(wx.VERTICAL)
        inner_sizer.Add(self.output, 1, wx.EXPAND | wx.ALL, 10)
        output_pad.SetSizer(inner_sizer)

        output_sizer = wx.BoxSizer(wx.HORIZONTAL)
        output_sizer.Add(output_pad, 1, wx.EXPAND | wx.ALL, 5)

        #============
        # grid_sizer
        # +-----------------------------------------------------------------------+
        # | Random quote          | Print every quote     | Statistics            |
        # |-----------------------|-----------------------|-----------------------|
        # | Random short quote    | Quote distribution    | Search                |
        # |-----------------------|-----------------------|-----------------------|
        # | Delay author toggle   | Clear window          | Book list by property |
        # +-----------------------------------------------------------------------+
        self.delay_author_toggle = wx.ToggleButton(panel, label="Random quotes: delay author")
        self.delay_author_toggle.SetValue(False)
        self.delay_author_toggle.SetToolTip("ON: Author appears after a delay\nOFF: Author appears immediately")
        self.delay_author_toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_delay_author)
        self.delay_author_toggle.SetBackgroundColour(wx.NullColour)

        btn1 = wx.Button(panel, label="Random quote")
        btn1.Bind(wx.EVT_BUTTON, lambda event: self.print_random_quote())
        btn2 = wx.Button(panel, label="Print every quote")
        btn2.Bind(wx.EVT_BUTTON, lambda event: self.print_every_quote())
        btn3 = wx.Button(panel, label="Statistics")
        btn3.Bind(wx.EVT_BUTTON, lambda event: self.print_statistics())
        btn4 = wx.Button(panel, label="Random short quote")
        btn4.Bind(wx.EVT_BUTTON, lambda event: self.print_random_quote("short"))
        btn5 = wx.Button(panel, label="Quote distribution")
        btn5.Bind(wx.EVT_BUTTON, lambda event: self.print_quote_distribution())
        btn6 = wx.Button(panel, label="Search")
        btn6.Bind(wx.EVT_BUTTON, lambda event: self.search())
        btn7 = wx.Button(panel, label="Clear window")
        btn7.Bind(wx.EVT_BUTTON, lambda event: self.clear())
        btn8 = wx.Button(panel, label="Book list by property")
        btn8.Bind(wx.EVT_BUTTON, lambda event: self.print_list_by_property())

        # set bigger font for buttons
        font = btn1.GetFont()
        font.SetPointSize(font.GetPointSize() + 1)

        grid_sizer = wx.GridSizer(3, 3, 10, 10)
        grid_buttons = [
            btn1, btn2, btn3,
            btn4, btn5, btn6,
            self.delay_author_toggle, btn7, btn8
        ]

        for btn in grid_buttons:
            grid_sizer.Add(btn, 0, wx.EXPAND)
            # width auto, height = 33 px
            btn.SetMinSize((-1, 33))
            btn.SetFont(font)

        #=============
        # reset_sizer
        # +-----------------------------------------------------------------------+
        # | Reset (full width)                                                    |
        # +-----------------------------------------------------------------------+
        reset_button = wx.Button(panel, label="Reset")
        reset_button.Bind(wx.EVT_BUTTON, lambda event: self.reset())
        reset_button.SetToolTip("Reset all settings and clear the output")
        reset_button.SetBackgroundColour(wx.Colour(220, 220, 220))
        reset_button.SetMinSize((-1, 36))
        reset_button.SetFont(font)
        reset_sizer = wx.BoxSizer(wx.HORIZONTAL)
        reset_sizer.Add(reset_button, 1, wx.EXPAND)

        #==================================
        # full window (VERTICAL main_sizer)
        # +-------------------------------------------------+
        # | header_sizer (dropdowns left, logo right)       |
        # +-------------------------------------------------+
        # | output_sizer (text output, expands vertically)  |
        # +-------------------------------------------------+
        # | grid_sizer (3x3 buttons)                        |
        # +-------------------------------------------------+
        # | reset_sizer (full-width reset button)           |
        # +-------------------------------------------------+
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(header_sizer, 0, wx.ALL | wx.EXPAND, 10)
        main_sizer.Add(output_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        main_sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(reset_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        panel.SetSizer(main_sizer)
        self.Center()
        self.Show()

    #=================================================
    # FUNCTION: toggle button changer
    #=================================================
    def on_toggle_delay_author(self, event):
        toggle = event.GetEventObject()
        if toggle.GetValue():
            # toggle is ON — change background color (light green)
            toggle.SetBackgroundColour(wx.Colour(180, 230, 180))
        else:
            # toggle is OFF — reset background and print pending author
            toggle.SetBackgroundColour(wx.NullColour)
            if self.pending_author_data:
                self._flush_pending_author()

        # refresh to apply color immediately
        toggle.Refresh()

    #=================================================
    # FUNCTION: folder/author dropdown change
    #=================================================
    def on_folder_or_author_change(self, event=None):
        widget = event.GetEventObject() if event else self.folders_dropdown
        chosen_folder = self.folders_dropdown.GetStringSelection()
        chosen_author = self.authors_dropdown.GetStringSelection()

        # update authors dropdown if folder changed and reset chosen author
        if widget == self.folders_dropdown:
            if chosen_folder == constants.ANY_FOLDER:
                # use full list (again)
                authors = [constants.ANY_AUTHOR] + self.authors_with_quotes
            else:
                # build list based on current folder (set comprehension)
                folder_authors = {
                    book.author
                    for book in book_collection.The_Collection
                    if book.folder == chosen_folder
                    and book.total_q > 0
                }
                folder_authors = sorted(folder_authors)
                authors = [constants.ANY_AUTHOR] + folder_authors

            self.authors_dropdown.Clear()
            self.authors_dropdown.AppendItems(authors)
            self.authors_dropdown.SetSelection(0)
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

        # update books dropdown
        self.books_dropdown.Clear()
        self.books_dropdown.AppendItems(self.filtered_books)
        self.books_dropdown.SetSelection(0)

    #=================================================
    # FUNCTION: log messages to the text box
    #=================================================
    def log(self, message):
        self.output.AppendText(message + "\n")

    #=================================================
    # FUNCTION: clear
    #=================================================
    def clear(self):
        # clear existing text
        self.output.Clear()

    #=================================================
    # FUNCTION: reset
    #=================================================
    def reset(self):
        dlg = wx.MessageDialog(
            self,
            "Are you sure you want to reset everything?",
            "Confirm Reset",
            wx.YES_NO | wx.ICON_WARNING
        )
        if dlg.ShowModal() == wx.ID_YES:
            # flush any pending delayed author print
            self._flush_pending_author(print_data=False)

            book_collection.build_the_collection()
            self.folders_dropdown.SetSelection(0)
            self.authors_dropdown.SetSelection(0)
            self.books_dropdown.SetSelection(0)
            # build full dropdown lists again
            self.on_folder_or_author_change()

            # reset toggle button to OFF visually and logically
            self.delay_author_toggle.SetValue(False)
            self.delay_author_toggle.SetBackgroundColour(wx.NullColour)
            self.delay_author_toggle.Refresh()
            self.clear()
        dlg.Destroy()

    #=================================================
    # FUNCTION: print wrapped text
    #=================================================
    def print_wrapped_text(self, text, min_width=20, padding=20):
        dc = wx.ClientDC(self.output)
        dc.SetFont(self.output.GetFont())

        avg_char_width = dc.GetTextExtent("X")[0]
        text_ctrl_width = self.output.GetSize().width - padding

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
        # if a delayed author is pending, show it now
        self._flush_pending_author()

        # get GUI values
        selected_title = self.books_dropdown.GetStringSelection()
        delay_author = self.delay_author_toggle.GetValue()

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

    def _print_author_now(self, book, quotes_left):
        self.log(f"\n{book.title}   / {quotes_left} left /")
        self.log(f"{'-' * len(book.title)}\n\n")

    def _schedule_author(self, book, quotes_left, quote_length, base_delay_ms=1000, ms_per_char=50):
        delay_ms = base_delay_ms + quote_length * ms_per_char
        # cap maximum delay to 60 seconds
        delay_ms = min(delay_ms, 60000)
        # store data in a tuple
        self.pending_author_data = (book, quotes_left)
        self.author_timer = wx.CallLater(delay_ms, self._print_pending_author)

    def _print_pending_author(self):
        if self.pending_author_data:
            # unpack the stored tuple
            book, quotes_left = self.pending_author_data
            self._print_author_now(book, quotes_left)

        self.pending_author_data = None
        self.author_timer = None

    def _flush_pending_author(self, print_data=True):
        if self.author_timer:
            self.author_timer.Stop()
            self.author_timer = None

        if print_data and self.pending_author_data:
            book, quotes_left = self.pending_author_data
            self._print_author_now(book, quotes_left)

        self.pending_author_data = None

    #=================================================
    # FUNCTION: print every quote
    #=================================================
    def print_every_quote(self):
        self.clear()

        selected_title = self.books_dropdown.GetStringSelection()
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
            header = f"{i + 1} / {len(quotes)}  (p.{quote.page})"
            self.log(header)
            self.print_wrapped_text(quote.text)
            self.log("")

    #=================================================
    # FUNCTION: print quote distribution
    #=================================================
    def print_quote_distribution(self):
        self.clear()

        # get the book
        selected_title = self.books_dropdown.GetStringSelection()
        if selected_title == constants.ANY_BOOK:
            self.log("Select a book from the list.")
            return
        book = book_utils.get_book_by_title(book_collection.The_Collection, selected_title)

        # header
        title = book.title
        self.log(title)
        self.log("-" * len(title))
        self.log("")

        # calculate columns based on control width
        dc = wx.ClientDC(self.output)
        dc.SetFont(self.output.GetFont())
        avg_char_width = dc.GetTextExtent("X")[0]
        ctrl_width_px = self.output.GetSize().width
        columns = book_utils.calculate_columns_from_width(ctrl_width_px, avg_char_width)
        rows = round(columns * 0.2)
        space = "   "

        # get distribution using utils
        mapped_distr = book_utils.compute_quote_distribution(book, columns=columns, rows=rows)

        # draw diagram
        self.log(f"{space}↑")
        for i in range(rows):
            row = ''.join('*' if mapped_distr[j] >= (rows - i) else ' ' for j in range(columns))
            self.log(f"{space}|{row}")

        self.log(f"{space}{'-' * columns}→")
        self.log(f"{space}1{' ' * (columns - len(str(book.pages_count)) + 1)}{book.pages_count}")
        self.log("")

    #=================================================
    # FUNCTION: print books list by property
    #=================================================
    def print_list_by_property(self):
        self.clear()

        dlg = wx.SingleChoiceDialog(
            self,
            "Select a property to sort/filter books by:",
            "Book Properties",
            constants.PROPERTIES,
            style=wx.CHOICEDLG_STYLE
        )

        if dlg.ShowModal() == wx.ID_OK:
            book_property = dlg.GetStringSelection()
            sorted_books = book_utils.sort_books_for_property(book_collection.The_Collection, book_property)
            folder = self.folders_dropdown.GetStringSelection()
            filtered_books = book_utils.filter_books_by_folder(sorted_books, folder)

            for book in filtered_books:
                line = book_utils.get_info_row_by_property(book, book_property, print_pages=(book_property == constants.PROP_PUBLISH_DATE))
                if line:
                    # only log if not None
                    self.log(f"  -->  {line}")

            # continued print for rating / finished list
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

        dlg.Destroy()

    #=================================================
    # FUNCTION: print statistics
    #=================================================
    def print_statistics(self):
        self.clear()
        # create auxiliary dictionaries
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
        self.log(f"{string}\n{'-' * len(string)}\n")
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

        # sort folders by total quotes (descending)
        folder_q_count = dict(sorted(folder_q_count.items(), key=lambda item: item[1], reverse=True))
        self.print_folder_dict(folder_q_count, book_collection.All_Quotes_Count)

        #=================================================
        # authors
        #=================================================
        self.log("")
        string = "Top 15 Authors"
        self.log(f"{string}\n{'-' * len(string)}")

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
        self.log("\n")
        string = "Top 30 most used words"
        self.log(f"\n{string}\n{'-' * len(string)}")

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
            # self.log(f" --> {count:3d} x {word}", end='')

            # find the book with the most occurrence of the word
            max_count = 0
            book_string = ""
            for book in book_collection.The_Collection:
                word_count = book_word_counts[book.title].get(word, 0)
                if word_count > max_count:
                    max_count = word_count
                    book_string = book.title

            # print related data in one line
            self.log(f" --> {count:3d} x {word}{' ' * (12-len(word))}{max_count:3d} / {book_string}")

    def print_stat_line(self, string, value, blank_line=False):
        self.log(f"{string}  {'-' * (48-len(string))}>  {value}")
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
        self.clear()
        # popup for user input
        dlg = wx.TextEntryDialog(
            self,
            message="Enter at least 3 characters:",
            caption="Search"
        )

        if dlg.ShowModal() == wx.ID_OK:
            str_to_search = dlg.GetValue().strip().lower()
        else:
            # user cancelled
            dlg.Destroy()
            return

        dlg.Destroy()

        # check length
        if len(str_to_search) < 3:
            self.log("Incorrect input. Please enter at least 3 characters.\n")
            return

        selected_title = self.books_dropdown.GetStringSelection()
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
                        self.log(f"{book.title}\n{'-' * len(book.title)}")
                        match_in_book = True

                    # highlight the search term by uppercasing (you could also add color later)
                    highlighted_text = self.highlight(quote.text, str_to_search)
                    self.print_wrapped_text(highlighted_text)
                    self.log('\n')

                    # count all occurrences in the quote
                    counter += len(re.findall(str_to_search, quote_text))

        # print result summary
        result = f"Matched {counter} time{'s' if counter != 1 else ''}."
        self.log(result if counter else "No match found.")
        if counter:
            self.log('-' * len(result))
        self.log('\n')

    def highlight(self, text, term):
        # replace all occurrences of term (case-insensitive) with uppercase
        return re.sub(re.escape(term), lambda m: m.group(0).upper(), text, flags=re.IGNORECASE)

#=================================================
# MYAPP
#=================================================
class MyApp(wx.App):
    def __init__(self, error=None, *args, **kwargs):
        self.error = error
        super().__init__(*args, **kwargs)

    def OnInit(self):
        self.frame = MainFrame()
        if self.error:
            self.frame.log(f"Error reading JSON file: {self.error}")
        self.frame.Show()
        return True

#=================================================
# MAIN
#=================================================
if __name__ == "__main__":
    error = book_collection.build_the_collection()
    app = MyApp(error=error)
    app.MainLoop()
