#=================================================
# IMPORT
#=================================================
import book_utils
import os
import tkinter as tk

from book_collection import BookCollection, Book
from collections.abc import Iterator
from constants_loader import constants
from tkinter import ttk, messagebox, font

#=================================================
# FILTER PANEL
#=================================================
class FilterPanel(ttk.Frame):

    #=================================================
    # type hints
    #=================================================
    folder_label: ttk.Label
    author_label: ttk.Label
    book_label: ttk.Label
    folders_dropdown: ttk.Combobox
    authors_dropdown: ttk.Combobox
    books_dropdown: ttk.Combobox

    def __init__(self, parent, label_font: font.Font):
        super().__init__(parent)

        # folder/author/book filters (widgets belong to this Frame and are arranged in _build_layout)
        self.folder_label = ttk.Label(self, text="FOLDER", font=label_font)
        self.author_label = ttk.Label(self, text="AUTHOR", font=label_font)
        self.book_label = ttk.Label(self, text="BOOK", font=label_font)

        self.folders_dropdown = ttk.Combobox(self)
        self.authors_dropdown = ttk.Combobox(self)
        self.books_dropdown = ttk.Combobox(self)

        self._build_layout()

    def _build_layout(self) -> None:
        grid_opts = {"column": 0, "padx": (0, 20), "pady": 6, "sticky": "w"}
        self.folder_label.grid(row=0, **grid_opts)
        self.author_label.grid(row=1, **grid_opts)
        self.book_label.grid(row=2, **grid_opts)

        self.folders_dropdown.grid(row=0, column=1, sticky="ew")
        self.authors_dropdown.grid(row=1, column=1, sticky="ew")
        self.books_dropdown.grid(row=2, column=1, sticky="ew")
        # allow dropdown widgets (in column 1) to stretch when space is available
        self.columnconfigure(1, weight=1)

    def set_folders_list(self, folders: list[str]) -> None:
        self.folders_dropdown["values"] = folders

    def set_authors_list(self, authors: list[str]) -> None:
        self.authors_dropdown["values"] = authors

    def set_books_list(self, books: list[str]) -> None:
        self.books_dropdown["values"] = books

    def select_first_all(self) -> None:
        self.select_first_folder()
        self.select_first_author()
        self.select_first_book()

    def select_first_folder(self) -> None:
        self._select_first_value(self.folders_dropdown)

    def select_first_author(self) -> None:
        self._select_first_value(self.authors_dropdown)

    def select_first_book(self) -> None:
        self._select_first_value(self.books_dropdown)

    def _select_first_value(self, combobox: ttk.Combobox) -> None:
        if combobox["values"]:
            combobox.current(0)

    def set_dropdowns_font(self, dropdown_font: font.Font) -> None:
        for dropdown in (
            self.folders_dropdown,
            self.authors_dropdown,
            self.books_dropdown,
        ):
            dropdown.configure(font=dropdown_font)

    def set_on_change_callback(self, callback) -> None:
        self.folders_dropdown.bind("<<ComboboxSelected>>", lambda e: callback("folder"))
        self.authors_dropdown.bind("<<ComboboxSelected>>", lambda e: callback("author"))
        self.books_dropdown.bind("<<ComboboxSelected>>", lambda e: callback("book"))

    @property
    def selected_folder(self) -> str:
        return self.folders_dropdown.get()

    @property
    def selected_author(self) -> str:
        return self.authors_dropdown.get()

    @property
    def selected_book(self) -> str:
        return self.books_dropdown.get()

#=================================================
# MAIN WINDOW
#=================================================
class MainWindow(tk.Tk):

    #=================================================
    # type hints
    #=================================================
    collection: BookCollection
    filtered_books: list[str]
    authors_with_quotes: list[str]

    #===================
    # output state
    #===================
    quote_printed: bool
    book_header_printed: bool
    pending_author_data: tuple[Book, int] | None
    author_timer_id: str | None
    quotes_remaining_var: tk.StringVar

    #===================
    # UI elements
    #===================
    header_frame: ttk.Frame
    filters: FilterPanel
    logo_frame: ttk.Frame
    q_counter_frame: ttk.Frame
    text_frame: ttk.Frame
    text_output: tk.Text
    buttons_frame: ttk.Frame

    every_q_btn: ttk.Button
    random_q_btn: ttk.Button
    delay_author_btn: ttk.Checkbutton
    delay_author_toggle: tk.BooleanVar
    clear_btn: ttk.Button
    reset_btn: ttk.Button

    #===================
    # helpers
    #===================
    _book_quote_count: int
    _quote_iter: Iterator

    #=================================================
    # initialization
    #=================================================
    def __init__(self, collection: BookCollection):
        super().__init__()

        #=================================================
        # instance attributes
        #=================================================
        self.collection = collection
        self.filtered_books = []
        self.authors_with_quotes = []
        self.quotes_remaining_var = tk.StringVar(value=f"{collection.all_quotes_count}")

        self.quote_printed = False
        self.book_header_printed = False
        self.pending_author_data = None
        # Tkinter "timer" placeholder (stores after() ID)
        self.author_timer_id = None

        #=================================================
        # set up Font objects for the GUI
        #=================================================
        self.default_font: font.Font = font.nametofont("TkDefaultFont").copy()
        self.button_font: font.Font = font.nametofont("TkDefaultFont").copy()
        self.default_font.configure(size=10)
        self.button_font.configure(size=11)

        #=================================================
        # call init and build functions
        #=================================================
        self._init_window()
        self._init_sub_frames()
        self._init_data()
        self._init_filters()
        self._init_buttons()
        self._init_signals()
        self._build_header_frame()
        self._build_text_frame()
        self._build_buttons_frame()

    #=================================================
    # main window
    #=================================================
    def _init_window(self) -> None:
        self.title("mini-gui")

        # add icon if available
        icon_path = "media/icon.png"
        if os.path.exists(icon_path):
            try:
                self.icon_img = tk.PhotoImage(file=icon_path)
                self.iconphoto(True, self.icon_img)
            except Exception as e:
                print(f"Warning: Could not load icon: {e}")
        else:
            print(f"Warning: Icon file not found: {icon_path}")

        # main panel
        self.set_default_window_size()
        self.panel = ttk.Frame(self)
        self.panel.pack(fill="both", expand=True)

    def set_default_window_size(self):
        width = 750
        height = 650

        # get screen size
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # calculate top-left corner coordinates and set geometry
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    #=================================================
    # sub frames
    #=================================================
    def _init_sub_frames(self) -> None:
        self.header_frame = ttk.Frame(self.panel)
        self.text_frame = ttk.Frame(self.panel)
        self.buttons_frame = ttk.Frame(self.panel)

        # grid and configure main panel
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.text_frame.grid(row=1, column=0, sticky="nsew", padx=15)
        self.buttons_frame.grid(row=2, column=0, sticky="ew", pady=18)
        self.panel.rowconfigure(1, weight=1)
        self.panel.columnconfigure(0, weight=1)

        # create FilterPanel (manages filter dropdowns and selection logic)
        self.filters = FilterPanel(self.header_frame, self.default_font)
        # create further sub-frames
        self.q_counter_frame = ttk.Frame(self.header_frame)
        self.logo_frame = ttk.Frame(self.header_frame)

        # grid and configure header frame
        self.filters.grid(row=0, column=0, sticky="ew", padx=(25, 0))
        self.logo_frame.grid(row=0, column=1, sticky="ew", padx=0)
        self.q_counter_frame.grid(row=0, column=2)
        self.header_frame.columnconfigure(0, weight=15)
        self.header_frame.columnconfigure(1, weight=10)
        self.header_frame.columnconfigure(2, weight=0)

    #=================================================
    # data preparation
    #=================================================
    def _init_data(self) -> None:
        authors_set = set()
        for book in self.collection.books:
            if book.total_quotes > 0:
                self.filtered_books.append(book.title)
                authors_set.add(book.author)
        self.authors_with_quotes = sorted(authors_set)

    #=================================================
    # ComboBox filters (dropdowns)
    #=================================================
    def _init_filters(self) -> None:
        self.filters.set_dropdowns_font(self.default_font)

        self.filters.set_folders_list(
            [constants.ANY_FOLDER] + sorted(list(self.collection.folders.keys()))
        )

        self.filters.set_authors_list(
            [constants.ANY_AUTHOR] + self.authors_with_quotes
        )

        self.filters.set_books_list(
            [constants.ANY_BOOK] + self.filtered_books
        )

        self.filters.select_first_all()

    #=================================================
    # init buttons
    #=================================================
    def _init_buttons(self) -> None:
        # custom style
        style = ttk.Style()
        style.configure("Big.TButton", font=self.button_font, padding=(15,15))

        self.every_q_btn = ttk.Button(
            self.buttons_frame,
            text="Print every quote",
            style="Big.TButton"
        )

        self.random_q_btn = ttk.Button(
            self.buttons_frame,
            text="Random quote",
            style="Big.TButton"
        )

        # this will be a special Tkinter variable
        self.delay_author_toggle = tk.BooleanVar(value=False)
        self.delay_author_btn = tk.Checkbutton(
            self.buttons_frame,
            text="Delay author",
            variable=self.delay_author_toggle,
            font=self.default_font,
        )

        self.clear_btn = ttk.Button(
            self.buttons_frame,
            text="Clear",
            style="Big.TButton"
        )

        self.reset_btn = ttk.Button(
            self.buttons_frame,
            text="Reset",
            style="Big.TButton"
        )

    #=================================================
    # signals (event bindings)
    #=================================================
    def _init_signals(self) -> None:
        # this method binds change callback for all comboboxes
        self.filters.set_on_change_callback(self._on_dropdown_change)

        self.every_q_btn.configure(command=self.print_every_quote)
        self.random_q_btn.configure(command=self.print_random_quote)
        self.delay_author_btn.configure(command=self._on_delay_author_toggle)
        self.clear_btn.configure(command=self.clear_text_output)
        self.reset_btn.configure(command=self.reset)

    #=================================================
    # header frame
    #=================================================
    def _build_header_frame(self) -> None:
        # filters object (FilterPanel instance) was already created
        # and positioned in header grid, add logo next to them
        string = f"== The Collection =="
        logo_text = f"{'=' * len(string)}\n{string}\n{'=' * len(string)}"
        logo = ttk.Label(
            self.logo_frame,
            text=logo_text,
            font=("Consolas", 14),
            anchor="center"
        )
        logo.grid(row=0, column=1, sticky="ew")
        self.logo_frame.columnconfigure(0, weight=1)
        self.logo_frame.columnconfigure(1, weight=0)
        self.logo_frame.columnconfigure(2, weight=1)

        # create labels for quotes remaining counter
        q_counter_title = ttk.Label(
            self.q_counter_frame,
            text="Quotes\nremaining",
            font=self.default_font,
            justify="center"
        )
        q_counter_value = ttk.Label(
            self.q_counter_frame,
            textvariable=self.quotes_remaining_var,
            font=self.default_font,
            width=8,
            anchor="center",
            relief="sunken"
        )
        q_counter_title.grid(row=0, column=0, padx=(0,25), pady=(0,5))
        q_counter_value.grid(row=1, column=0, padx=(0,25), pady=(0,5))

    #=================================================
    # text output
    #=================================================
    def _build_text_frame(self) -> None:
        # create text widget and scrollbar
        text_font = font.Font(family="Consolas", size=13)
        self.text_output = tk.Text(
            self.text_frame,
            wrap="word",
            state="disabled",
            font=text_font,
            padx=15,
            pady=15,
            bg="#F0E6C8"
        )
        scrollbar = ttk.Scrollbar(self.text_frame, orient="vertical", command=self.text_output.yview)
        self.text_output.configure(yscrollcommand=scrollbar.set)

        # pack text widget and pack scrollbar to the right
        self.text_output.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # give extra space to text widget, scrollbar column stays fixed
        self.text_frame.grid_rowconfigure(0, weight=1)
        self.text_frame.grid_columnconfigure(0, weight=1)

    #=================================================
    # button frame
    #=================================================
    def _build_buttons_frame(self) -> None:
        # left buttons
        self.every_q_btn.grid(row=0, column=0, padx=(25, 0), sticky="ew")
        self.random_q_btn.grid(row=0, column=1, padx=(15, 0), sticky="ew")
        self.delay_author_btn.grid(row=0, column=2, padx=(15, 0))
        # right buttons
        self.clear_btn.grid(row=0, column=4, padx=(15, 0), sticky="ew")
        self.reset_btn.grid(row=0, column=5, padx=(15, 25), sticky="ew")

        self.buttons_frame.columnconfigure(0, weight=1)  # every quote
        self.buttons_frame.columnconfigure(1, weight=1)  # random quote
        self.buttons_frame.columnconfigure(2, weight=0)  # toggle
        self.buttons_frame.columnconfigure(3, weight=10) # spacer
        self.buttons_frame.columnconfigure(4, weight=1)  # clear
        self.buttons_frame.columnconfigure(5, weight=1)  # reset

    #=================================================
    # log messages to the text widget
    #=================================================
    def log(self, message: str, scroll_to_end: bool = True) -> None:
        self.text_output.config(state="normal")
        self.text_output.insert("end", f"{message}\n")
        if scroll_to_end:
            self.text_output.see("end")
        self.text_output.config(state="disabled")

    #=================================================
    # print random quote
    #=================================================
    def print_random_quote(self) -> None:
        # print any remaining author data
        self._flush_pending_author()

        # get dropdown selections
        selected_title = self.filters.selected_book
        is_book_selected = selected_title != constants.ANY_BOOK
        delay_author = self.delay_author_toggle.get()

        book, message = book_utils.get_book_for_random_quote(
            self.collection.books,
            selected_title,
            self.filtered_books
        )

        if book is None:
            self.log(message)
            return

        # add space before previous print (but not before the first)
        if self.quote_printed:
            self.log("\n")
        else:
            self.clear_text_output()

        # print book header if a particular book is selected
        if is_book_selected and not self.book_header_printed:
            if self.quote_printed:
                # add an extra empty line for better separation
                self.log("")
            self.log(f"{book.title}", scroll_to_end=True)
            self.log(f"{'-'*len(book.title)}\n", scroll_to_end=True)
            self.book_header_printed = True

        # get the random quote and print it
        random_quote, quotes_left_in_book = book_utils.get_random_quote(book)
        self.log(random_quote.text)
        self.quote_printed = True

        if not is_book_selected:
            if not delay_author:
                self._print_author_now(book, quotes_left_in_book)
            else:
                self._schedule_author(book, quotes_left_in_book, len(random_quote.text))

        # call counter update
        self._update_quotes_ui_counter()

    def _print_author_now(
        self,
        book: Book,
        quotes_left_in_book: int,
        scroll_to_end: bool = True
    ) -> None:
        self.log(f"\n{book.title}   / {quotes_left_in_book} left /", scroll_to_end)
        self.log(f"{'-'*len(book.title)}", scroll_to_end)

    def _schedule_author(
        self,
        book: Book,
        quotes_left_in_book: int,
        quote_length: int,
        base_delay_ms: int = 1000,
        ms_per_char: int = 50
    ) -> None:
        delay_ms = min(base_delay_ms + quote_length * ms_per_char, 60000)
        self.pending_author_data = (book, quotes_left_in_book)

        # stop previous timer if running
        if self.author_timer_id is not None:
            self.after_cancel(self.author_timer_id)

        # start the timer (id is like: "after#0", "after#1", etc.)
        # Type checker warning is incorrect — no extra arguments are needed here
        self.author_timer_id = self.after(delay_ms, self._print_pending_author)

    def _print_pending_author(self) -> None:
        if self.pending_author_data:
            # unpack the stored tuple
            book, quotes_left_in_book = self.pending_author_data
            self._print_author_now(book, quotes_left_in_book, scroll_to_end=False)
        self.pending_author_data = None
        self.author_timer_id = None

    def _flush_pending_author(self, print_data: bool = True) -> None:
        if self.author_timer_id is not None:
            self.after_cancel(self.author_timer_id)
            self.author_timer_id = None
        if print_data and self.pending_author_data:
            book, quotes_left_in_book = self.pending_author_data
            self._print_author_now(book, quotes_left_in_book)
        self.pending_author_data = None

    def _on_delay_author_toggle(self) -> None:
        checked = self.delay_author_toggle.get()
        if not checked:
            if self.pending_author_data:
                self._flush_pending_author()
            else:
                # make already printed author visible
                self.text_output.see("end")

    #=================================================
    # print every quote
    #=================================================
    def print_every_quote(self) -> None:
        # set back clear state
        self.clear_text_output()
        self._update_quotes_ui_counter(use_book_total=True)

        selected_title = self.filters.selected_book
        if selected_title == constants.ANY_BOOK:
            self.log("Select a book from the list.")
            return

        book = book_utils.get_book_by_title(self.collection.books, selected_title)
        if book is None:
            self.log("Book not found.")
            return

        # book exists, get quotes for printing
        quotes = book_utils.get_quotes_sorted_by_page(book)
        self.log(book.title)
        self.log('-' * len(book.title))

        # setup async iteration state and start the loop
        self._book_quote_count = len(quotes)
        # enumerate(quotes) produces (index, quote) pairs
        # iter() creates the iterator over them
        self._quote_iter = iter(enumerate(quotes))
        self._print_next_quote()

    def _print_next_quote(self) -> None:
        try:
            i, quote = next(self._quote_iter)
        except StopIteration:
            # finished
            self.text_output.see("1.0")
            self._set_quotes_ui_counter(0)
            return

        header = f"{i + 1} / {self._book_quote_count}  (p.{quote.page})"
        self.log(header)
        self.log(quote.text)
        if i < (self._book_quote_count - 1):
            self.log("\n")
        self._set_quotes_ui_counter(self._book_quote_count  - i)

        # schedule next iteration
        self.after(5, self._print_next_quote)

    #=================================================
    # quotes remaining counter
    #=================================================
    def _update_quotes_ui_counter(self, use_book_total=False) -> None:
        selected_book = self.filters.selected_book

        if selected_book == constants.ANY_BOOK:
            chosen_folder = self.filters.selected_folder
            chosen_author = self.filters.selected_author
            quotes_count = sum(
                book.remaining_quote_count
                for book in self.collection.books
                if self._book_matches_filters(book, chosen_folder, chosen_author)
            )
        else:
            book = book_utils.get_book_by_title(self.collection.books, selected_book)
            if book:
                quotes_count = (
                    book.total_quotes
                    if use_book_total
                    else book.remaining_quote_count
                )
            else:
                quotes_count = 0

        self._set_quotes_ui_counter(quotes_count)

    def _set_quotes_ui_counter(self, value: int) -> None:
        self.quotes_remaining_var.set(str(value))

    #=================================================
    # clear text output
    #=================================================
    def clear_text_output(self) -> None:
        self._flush_pending_author(print_data=False)
        self.quote_printed = False
        self.book_header_printed = False
        self.text_output.config(state="normal")
        self.text_output.delete("1.0", "end")
        self.text_output.config(state="disabled")
        self._update_quotes_ui_counter()

    #=================================================
    # reset
    #=================================================
    def reset(self) -> None:
        reply = messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset everything?",
            parent=self
        )

        if not reply:
            return

        # rebuild collection and reset dropdowns
        self.collection.build_the_collection()
        self.filters.select_first_all()

        # build full dropdown lists again
        self._on_dropdown_change("folder")

        # in Tkinter:
        # command= runs only on user interaction (mouse/keyboard click)
        # .set() changes the associated BooleanVar value only
        # .set() does NOT trigger the command callback
        self.delay_author_toggle.set(False)
        self.clear_text_output()
        self.set_default_window_size()

    #=================================================
    # combobox change
    #=================================================
    def _on_dropdown_change(self, source: str) -> None:
        chosen_folder = self.filters.selected_folder

        if source == "book":
            self._update_quotes_ui_counter()
            # book name should be printed before the first quote
            self.book_header_printed = False
            return

        # update authors dropdown, if folder changed
        if source == "folder":
            if chosen_folder == constants.ANY_FOLDER:
                authors = [constants.ANY_AUTHOR] + self.authors_with_quotes
            else:
                folder_authors = {
                    book.author
                    for book in self.collection.books
                    if book.folder == chosen_folder
                    and book.total_quotes > 0
                }
                folder_authors = sorted(folder_authors)
                authors = [constants.ANY_AUTHOR] + folder_authors

            self.filters.set_authors_list(authors)
            self.filters.select_first_author()

        # gather books for dropdown into a filtered books list
        self.filtered_books = [constants.ANY_BOOK]

        for book in self.collection.books:
            # check selected folder and/or author for matching books
            if self._book_matches_filters(book, chosen_folder, self.filters.selected_author) and book.total_quotes > 0:
                self.filtered_books.append(book.title)

        # set gathered list and reset dropdown
        self.filters.set_books_list(self.filtered_books)
        self.filters.select_first_book()
        self._update_quotes_ui_counter()

    #=================================================
    # filter match for a book instance
    #=================================================
    @staticmethod
    def _book_matches_filters(book, chosen_folder, chosen_author) -> bool:
        return (
            (chosen_folder == constants.ANY_FOLDER or book.folder == chosen_folder)
            and (chosen_author == constants.ANY_AUTHOR or book.author == chosen_author)
        )

#=================================================
# MAIN
#=================================================
if __name__ == "__main__":
    print("mini-gui is running...")
    The_Collection = BookCollection()
    error = The_Collection.build_the_collection()
    window = MainWindow(The_Collection)
    if error:
        window.log(f"Error reading JSON file: {error}\n")
    else:
        window.log(
            f"This collection has {window.collection.all_quotes_count}"
            f" quotes from {len(window.filtered_books)} books.\n\n"
        )
    window.mainloop()
