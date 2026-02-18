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
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font

#=================================================
# MAIN WINDOW
#=================================================
class MainWindow(tk.Tk):

    #=================================================
    # initialization
    #=================================================
    def __init__(self):
        super().__init__()

        self.default_font = font.nametofont("TkDefaultFont").copy()
        self.big_font = font.nametofont("TkDefaultFont").copy()
        self.default_font.configure(size=10)
        self.big_font.configure(size=12)

        self._init_window()
        self._init_sub_frames()
        self._init_data()
        self._init_state()
        self._init_filters()
        self._init_buttons()
        self._init_signals()
        self._build_main_frame()
        self.mainloop()

    #=================================================
    # main window
    #=================================================
    def _init_window(self):
        self.title("mini-gui")

        # desired window size
        width = 1024
        height = 768

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
    def _init_sub_frames(self):
        self.header_frame = ttk.Frame(self.panel)
        self.header_frame.pack(side="top", fill="x", padx=10, pady=10)

        self.text_frame = ttk.Frame(self.panel)
        self.text_frame.pack(fill="both", expand=True, padx=(15, 15))

        self.buttons_frame = ttk.Frame(self.panel)
        self.buttons_frame.pack(fill="x", pady=(20,20))

    #=================================================
    # data preparation
    #=================================================
    def _init_data(self):
        self.filtered_books = []
        authors_set = set()
        for book in book_collection.The_Collection:
            if book.total_q > 0:
                self.filtered_books.append(book.title)
                authors_set.add(book.author)
        self.authors_with_quotes = sorted(authors_set)

    #=================================================
    # default state
    #=================================================
    def _init_state(self):
        self.quote_printed = False
        self.pending_author_data = None

        # Tkinter "timer" placeholder (stores after() ID)
        self.author_timer_id = None

    #=================================================
    # ComboBox filters (dropdowns)
    #=================================================
    def _init_filters(self):
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
        for cb in (self.folders_dropdown, self.authors_dropdown, self.books_dropdown):
            cb.current(0)

    #=================================================
    # init buttons
    #=================================================
    def _init_buttons(self):
        # custom style
        style = ttk.Style()
        style.configure("Big.TButton", font=self.big_font, padding=(15,15))

        # this will be a special Tkinter variable
        self.delay_author_toggle = tk.BooleanVar(value=False)
        self.delay_author_btn = tk.Checkbutton(
            self.buttons_frame,
            text="Random quotes:\ndelay author",
            variable=self.delay_author_toggle,
            font=self.default_font,
            command=self._on_delay_author_toggle
        )

        # just three buttons
        self.random_q_btn = ttk.Button(
            self.buttons_frame,
            text="Random quote",
            command=self.print_random_quote,
            style="Big.TButton"
        )

        self.every_q_btn = ttk.Button(
            self.buttons_frame,
            text="Print every quote",
            command=self.print_every_quote,
            style="Big.TButton"
        )

        self.reset_btn = ttk.Button(
            self.buttons_frame,
            text="Reset",
            command=self.reset,
            style="Big.TButton"
        )
        
    def _on_delay_author_toggle(self):
        checked = self.delay_author_toggle.get()
        if not checked and self.pending_author_data:
            self._flush_pending_author()

    #=================================================
    # signals (event bindings)
    #=================================================
    def _init_signals(self):
        self.folders_dropdown.bind("<<ComboboxSelected>>", lambda e: self.on_folder_or_author_change("folder"))
        self.authors_dropdown.bind("<<ComboboxSelected>>", lambda e: self.on_folder_or_author_change("author"))

    #=================================================
    # header layout
    #=================================================
    def _build_header_frame(self):
        # pack into parent frame, which is header frame
        self.filters_frame.pack(side="left", fill="x", padx=25)

        # populate filters_frame with labels and dropdowns
        folder_label = ttk.Label(self.filters_frame, text="FOLDER", font=self.default_font)
        author_label = ttk.Label(self.filters_frame, text="AUTHOR", font=self.default_font)
        book_label = ttk.Label(self.filters_frame, text="BOOK", font=self.default_font)
        folder_label.grid(row=0, column=0, padx=(0,20), pady=6, sticky="w")
        author_label.grid(row=1, column=0, padx=(0,20), pady=6, sticky="w")
        book_label.grid(row=2, column=0, padx=(0,20), pady=6, sticky="w")
        self.folders_dropdown.grid(row=0, column=1)
        self.authors_dropdown.grid(row=1, column=1)
        self.books_dropdown.grid(row=2, column=1)

        # logo on the right
        string = f"== The Collection =="
        logo_text = f"{'=' * len(string)}\n{string}\n{'=' * len(string)}"
        logo_frame = ttk.Frame(self.header_frame)
        logo_label = ttk.Label(logo_frame, text=logo_text, font=("Consolas", 14), anchor="center").pack()
        logo_frame.pack(side="right", fill="x", padx=75)

    #=================================================
    # text output
    #=================================================
    def _build_text_frame(self):
        # create text widget and scrollbar
        text_font = font.Font(family="Consolas", size=12)
        self.text_output = tk.Text(
            self.text_frame,
            wrap="word",
            state="disabled",
            font=text_font,
            padx=15,
            pady=15,
            bg="#F0E6C8"
        )
        self.scrollbar = ttk.Scrollbar(self.text_frame, orient="vertical", command=self.text_output.yview)
        self.text_output.configure(yscrollcommand=self.scrollbar.set)
        
        # pack text widget and pack scrollbar to the right
        self.text_output.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    #=================================================
    # button grid
    #=================================================
    def _build_button_frame(self):
        self.every_q_btn.pack(side="left", padx=25)
        self.random_q_btn.pack(side="left", padx=10)
        self.delay_author_btn.pack(side="left", padx=10)
        self.reset_btn.pack(side="right", padx=25)

    #=================================================
    # main layout
    #=================================================
    def _build_main_frame(self):
        self._build_header_frame()
        self._build_text_frame()
        self._build_button_frame()

    #=================================================
    # log messages to the text widget
    #=================================================
    def log(self, message):
        self.text_output.config(state="normal")
        self.text_output.insert("end", f"{message}\n")
        self.text_output.see("end")
        self.text_output.config(state="disabled")

    #=================================================
    # print random quotes
    #=================================================
    def print_random_quote(self, length="any"):
        # print any remaining author data
        self._flush_pending_author()

        selected_title = self.books_dropdown.get()
        delay_author = self.delay_author_toggle.get()

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

        if not delay_author:
            self._print_author_now(book, quotes_left)
        else:
            self._schedule_author(book, quotes_left, len(random_quote.text))

    def _print_author_now(self, book, quotes_left):
        self.log(f"\n{book.title}   / {quotes_left} left /")
        self.log(f"{'-'*len(book.title)}")

    def _schedule_author(self, book, quotes_left, quote_length, base_delay_ms=1000, ms_per_char=50):
        delay_ms = min(base_delay_ms + quote_length * ms_per_char, 60000)
        self.pending_author_data = (book, quotes_left)
    
        # stop previous timer if running
        if self.author_timer_id is not None:
            self.after_cancel(self.author_timer_id)
    
        # start the timer
        self.author_timer_id = self.after(delay_ms, self._print_pending_author)

    def _print_pending_author(self):
        if self.pending_author_data:
            # unpack the stored tuple
            book, quotes_left = self.pending_author_data
            self._print_author_now(book, quotes_left)
        self.pending_author_data = None
        self.author_timer_id = None  

    def _flush_pending_author(self, print_data=True):
        if self.author_timer_id is not None:
            self.after_cancel(self.author_timer_id)
            self.author_timer_id = None
        if print_data and self.pending_author_data:
            book, quotes_left = self.pending_author_data
            self._print_author_now(book, quotes_left)
        self.pending_author_data = None

    #=================================================
    # print random quote
    #=================================================
    def print_every_quote(self):
        self.clear()

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

        for i, quote in enumerate(quotes):
            header = f"{i+1} / {len(quotes)}  (p.{quote.page})"
            self.log(header)
            self.log(quote.text)
            self.log("")
            
    #=================================================
    # clear
    #=================================================
    def clear(self):
        self.text_output.config(state="normal")
        self.text_output.delete("1.0", "end")
        self.text_output.config(state="disabled")
        
    #=================================================
    # reset
    #=================================================
    def reset(self):
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
        # `command=` runs only on user interaction (mouse/keyboard click)
        # `.set()` changes the associated BooleanVar value only
        # `.set()` does NOT trigger the `command` callback
        self.delay_author_toggle.set(False)
        
        self.quote_printed = False
        self.clear()
        
    def on_folder_or_author_change(self, source):
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
            if chosen_folder != constants.ANY_FOLDER and book.folder != chosen_folder:
                continue
            if chosen_author != constants.ANY_AUTHOR and book.author != chosen_author:
                continue
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
        window.text_output.config(state="normal")
        window.text_output.insert("end", f"Error reading JSON file: {error}\n")
        window.text_output.config(state="disabled")