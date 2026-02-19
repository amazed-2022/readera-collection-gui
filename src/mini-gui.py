#=================================================
# IMPORT
#=================================================
import book_collection
import book_utils
from constants_loader import constants
import tkinter as tk
from tkinter import ttk, messagebox, font

#=================================================
# MAIN WINDOW
#=================================================
class MainWindow(tk.Tk):

    # attributes defined here would be class attributes, shared by all instances

    #=================================================
    # initialization
    #=================================================
    def __init__(self):
        super().__init__()

        #=================================================
        # instance attributes: type hints and init
        #=================================================
        self.filtered_books: list[str] = []
        self.authors_with_quotes: list[str] = []

        self.quote_printed: bool = False
        self.pending_author_data: tuple[book_collection.Book, int] | None = None
        # Tkinter "timer" placeholder (stores after() ID)
        self.author_timer_id: str | None = None

        self.header_frame: ttk.Frame
        self.filters_frame: ttk.Frame
        self.text_frame: ttk.Frame
        self.buttons_frame: ttk.Frame
        self.folders_dropdown: ttk.Combobox
        self.authors_dropdown: ttk.Combobox
        self.books_dropdown: ttk.Combobox

        self.text_output: tk.Text

        self.every_q_btn: ttk.Button
        self.random_q_btn: ttk.Button
        self.delay_author_btn: ttk.Button
        self.delay_author_toggle: tk.BooleanVar
        self.reset_btn: ttk.Button

        #=================================================
        # set up Font objects for the GUI
        #=================================================
        self.default_font: font.Font = font.nametofont("TkDefaultFont").copy()
        self.button_font: font.Font = font.nametofont("TkDefaultFont").copy()
        self.default_font.configure(size=10)
        self.button_font.configure(size=11)

        #=================================================
        # call init, build functions and start loop
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

        # desired window size
        width = 850
        height = 850

        # get screen size
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # calculate top-left corner coordinates and set geometry
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # main panel
        self.panel = ttk.Frame(self)
        self.panel.pack(fill="both", expand=True)

    #=================================================
    # sub frames
    #=================================================
    def _init_sub_frames(self) -> None:
        self.header_frame = ttk.Frame(self.panel)
        self.header_frame.pack(side="top", fill="x", padx=10, pady=10)

        self.text_frame = ttk.Frame(self.panel)
        self.text_frame.pack(side="top", fill="both", expand=True, padx=(15, 15))

        self.buttons_frame = ttk.Frame(self.panel)
        self.buttons_frame.pack(side="top", fill="x", pady=(20,20))

    #=================================================
    # data preparation
    #=================================================
    def _init_data(self) -> None:
        authors_set = set()
        for book in book_collection.The_Collection:
            if book.total_q > 0:
                self.filtered_books.append(book.title)
                authors_set.add(book.author)
        self.authors_with_quotes = sorted(authors_set)

    #=================================================
    # ComboBox filters (dropdowns)
    #=================================================
    def _init_filters(self) -> None:
        self.filters_frame = ttk.Frame(self.header_frame)
        self.folders_dropdown = ttk.Combobox(
            self.filters_frame,
            values=[constants.ANY_FOLDER] + sorted(list(book_collection.Folders.keys())),
            font=self.default_font,
            width=60
        )
        self.authors_dropdown = ttk.Combobox(
            self.filters_frame,
            values=[constants.ANY_AUTHOR] + self.authors_with_quotes,
            font=self.default_font,
            width=60
        )
        self.books_dropdown = ttk.Combobox(
            self.filters_frame,
            values=[constants.ANY_BOOK] + self.filtered_books,
            font=self.default_font,
            width=60
        )

        self.folders_dropdown.current(0)
        self.authors_dropdown.current(0)
        self.books_dropdown.current(0)

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

        # just three buttons
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
        self.folders_dropdown.bind("<<ComboboxSelected>>", lambda e: self.on_folder_or_author_change("folder"))
        self.authors_dropdown.bind("<<ComboboxSelected>>", lambda e: self.on_folder_or_author_change("author"))

        self.every_q_btn.configure(command=self.print_every_quote)
        self.random_q_btn.configure(command=self.print_random_quote)
        self.delay_author_btn.configure(command=self._on_delay_author_toggle)
        self.clear_btn.configure(command=self.clear_text_output)
        self.reset_btn.configure(command=self.reset)

    #=================================================
    # header frame
    #=================================================
    def _build_header_frame(self) -> None:
        # pack into parent frame, which is header frame
        self.filters_frame.pack(side="left", fill="x", padx=25)

        # populate filters_frame with labels and dropdowns
        folder_label = ttk.Label(self.filters_frame, text="FOLDER", font=self.default_font)
        author_label = ttk.Label(self.filters_frame, text="AUTHOR", font=self.default_font)
        book_label = ttk.Label(self.filters_frame, text="BOOK", font=self.default_font)
        grid_opts = {"column": 0, "padx": (0, 20), "pady": 6, "sticky": "w"}
        folder_label.grid(row=0, **grid_opts)
        author_label.grid(row=1, **grid_opts)
        book_label.grid(row=2, **grid_opts)
        self.folders_dropdown.grid(row=0, column=1)
        self.authors_dropdown.grid(row=1, column=1)
        self.books_dropdown.grid(row=2, column=1)

        # logo on the right
        string = f"== The Collection =="
        logo_text = f"{'=' * len(string)}\n{string}\n{'=' * len(string)}"
        logo_frame = ttk.Frame(self.header_frame)
        ttk.Label(logo_frame, text=logo_text, font=("Consolas", 14), anchor="center").pack()
        logo_frame.pack(side="left", fill="x", padx=20)

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
        self.text_output.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    #=================================================
    # button frame
    #=================================================
    def _build_buttons_frame(self) -> None:
        self.every_q_btn.pack(side="left", padx=(25, 0))
        self.random_q_btn.pack(side="left", padx=(15, 0))
        self.delay_author_btn.pack(side="left", padx=(15, 0))
        self.reset_btn.pack(side="right", padx=(0, 25))
        self.clear_btn.pack(side="right", padx=(0, 15))

    #=================================================
    # log messages to the text widget
    #=================================================
    def log(self, message: str) -> None:
        self.text_output.config(state="normal")
        self.text_output.insert("end", f"{message}\n")
        self.text_output.see("end")
        self.text_output.config(state="disabled")

    #=================================================
    # print random quotes
    #=================================================
    def print_random_quote(self) -> None:
        # print any remaining author data
        self._flush_pending_author()

        selected_title = self.books_dropdown.get()
        delay_author = self.delay_author_toggle.get()

        book, message = book_utils.get_book_for_random_quote(
            book_collection.The_Collection,
            selected_title,
            self.filtered_books
        )

        # add space before previous print (but not before the first)
        if self.quote_printed:
            self.log("\n")
        else:
            self.clear_text_output()
        self.quote_printed = True

        if book is None:
            self.log(message)
            return

        # get the random quote and print it
        random_quote, quotes_left = book_utils.get_random_quote(book)
        self.log(random_quote.text)

        if not delay_author:
            self._print_author_now(book, quotes_left)
        else:
            self._schedule_author(book, quotes_left, len(random_quote.text))

    def _print_author_now(self, book: book_collection.Book, quotes_left: int) -> None:
        self.log(f"\n{book.title}   / {quotes_left} left /")
        self.log(f"{'-'*len(book.title)}")

    def _schedule_author(
        self,
        book: book_collection.Book,
        quotes_left: int,
        quote_length: int,
        base_delay_ms: int = 1000,
        ms_per_char: int = 50
    ) -> None:
        delay_ms = min(base_delay_ms + quote_length * ms_per_char, 60000)
        self.pending_author_data = (book, quotes_left)

        # stop previous timer if running
        if self.author_timer_id is not None:
            self.after_cancel(self.author_timer_id)

        # start the timer
        # Type checker warning is incorrect — no extra arguments are needed here
        self.author_timer_id = self.after(delay_ms, self._print_pending_author)

    def _print_pending_author(self) -> None:
        if self.pending_author_data:
            # unpack the stored tuple
            book, quotes_left = self.pending_author_data
            self._print_author_now(book, quotes_left)
        self.pending_author_data = None
        self.author_timer_id = None

    def _flush_pending_author(self, print_data: bool = True) -> None:
        if self.author_timer_id is not None:
            self.after_cancel(self.author_timer_id)
            self.author_timer_id = None
        if print_data and self.pending_author_data:
            book, quotes_left = self.pending_author_data
            self._print_author_now(book, quotes_left)
        self.pending_author_data = None
        
    def _on_delay_author_toggle(self) -> None:
        checked = self.delay_author_toggle.get()
        if not checked and self.pending_author_data:
            self._flush_pending_author()

    #=================================================
    # print random quote
    #=================================================
    def print_every_quote(self) -> None:
        # set back clear state
        self.clear_text_output()

        selected_title = self.books_dropdown.get()
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

        num_of_quotes = len(quotes)
        for i, quote in enumerate(quotes):
            header = f"{i+1} / {num_of_quotes}  (p.{quote.page})"
            self.log(header)
            self.log(quote.text)
            if i < (num_of_quotes-1):
                self.log("\n")

    #=================================================
    # clear text output
    #=================================================
    def clear_text_output(self) -> None:
        self.quote_printed = False
        self.text_output.config(state="normal")
        self.text_output.delete("1.0", "end")
        self.text_output.config(state="disabled")

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
        book_collection.build_the_collection()
        self.folders_dropdown.current(0)
        self.authors_dropdown.current(0)
        self.books_dropdown.current(0)
        # build full dropdown lists again
        self.on_folder_or_author_change("folder")

        # in Tkinter:
        # command= runs only on user interaction (mouse/keyboard click)
        # .set() changes the associated BooleanVar value only
        # .set() does NOT trigger the command callback
        self.delay_author_toggle.set(False)
        self.clear_text_output()

    #=================================================
    # combobox change
    #=================================================
    def on_folder_or_author_change(self, source: str) -> None:
        chosen_folder = self.folders_dropdown.get()
        chosen_author = self.authors_dropdown.get()

        # update authors dropdown, if folder changed
        if source == "folder":
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

            self.authors_dropdown["values"] = authors
            self.authors_dropdown.current(0)
            chosen_author = constants.ANY_AUTHOR

        # update books dropdown
        self.filtered_books = [constants.ANY_BOOK]

        for book in book_collection.The_Collection:
            # skip books that don't match the selected folder
            if chosen_folder != constants.ANY_FOLDER and book.folder != chosen_folder:
                continue

            # skip books that don't match the selected author
            if chosen_author != constants.ANY_AUTHOR and book.author != chosen_author:
                continue

            # at this point, the book matches all filters
            if book.total_q > 0:
                self.filtered_books.append(book.title)

        self.books_dropdown["values"] = self.filtered_books
        self.books_dropdown.current(0)

#=================================================
# MAIN
#=================================================
if __name__ == "__main__":
    error = book_collection.build_the_collection()
    window = MainWindow()
    if error:
        window.log(f"Error reading JSON file: {error}\n")
    window.mainloop()


