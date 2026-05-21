#=================================================
# IMPORT
#=================================================
import book_utils

from book_collection import Book, Quote
from collections.abc import Iterator
from constants_loader import constants
from typing import Protocol

#=================================================
# PROTOCOL
#=================================================
class QuotePrinterAPI(Protocol):
    # output
    def log(self, message: str, scroll_to_bottom: bool = True) -> None: ...
    def clear_text_output(self) -> None: ...

    # scheduling
    def schedule(self, ms: int, callback) -> str | None: ...
    def cancel_timer(self, timer_id: str) -> None: ...

    # navigation
    def scroll_to_top(self) -> None: ...
    def scroll_to_bottom(self) -> None: ...

    # state
    def delay_author_enabled(self) -> bool: ...
    def update_quotes_ui_counter(self, use_book_total: bool = False) -> None: ...
    def set_quotes_ui_counter(self, value: int) -> None: ...

    # data access
    def get_selected_book_title(self) -> str: ...
    def get_collection_books(self) -> list[Book]: ...
    def get_filtered_books(self) -> list[str]: ...

#=================================================
# QUOTE PRINTER
#=================================================
class QuotePrinter:

    #=================================================
    # type hints
    #=================================================
    quote_printed: bool
    book_header_printed: bool

    pending_author_data: tuple[Book, int] | None
    author_timer_id: str | None

    book_quote_count: int
    quote_iter: Iterator[tuple[int, Quote]]

    #=================================================
    # initialization
    #=================================================
    def __init__(self, ui: QuotePrinterAPI):
        """
        # ui needs to provide:
        # - log(...)
        # - schedule(...)
        # - cancel_timer(...)
        # - scroll_to_top()
        # - scroll_to_bottom()
        # - delay_author_enabled()
        # - update_quotes_ui_counter()
        """
        self.ui = ui

        # set default state
        self.quote_printed = False
        self.book_header_printed = False
        self.pending_author_data = None
        # Tkinter "timer" placeholder (stores after() ID)
        self.author_timer_id = None

    #=================================================
    # print random quote
    #=================================================
    def print_random_quote(self, length: str = "any") -> None:
        # print any remaining author data
        self._flush_pending_author()

        # get dropdown selections
        selected_title = self.ui.get_selected_book_title()
        is_book_selected = selected_title != constants.ANY_BOOK
        delay_author = self.ui.delay_author_enabled()

        book, message = book_utils.get_book_for_random_quote(
            self.ui.get_collection_books(),
            selected_title,
            self.ui.get_filtered_books(),
            length
        )

        # something went wrong, return early
        if book is None:
            if message is not None:
                self.ui.log(message)
            return

        # add space before previous print (but not before the first)
        if self.quote_printed:
            self.ui.log("\n")
        else:
            self.ui.clear_text_output()

        # print book header if a particular book is selected
        if is_book_selected and not self.book_header_printed:
            if self.quote_printed:
                # add an extra empty line for better separation
                self.ui.log("")
            self.ui.log(f"{book.title}", scroll_to_bottom=True)
            self.ui.log(f"{'-'*len(book.title)}\n", scroll_to_bottom=True)
            self.book_header_printed = True

        # get the random quote and print it
        random_quote, quotes_left_in_book = book_utils.get_random_quote(book)

        # something went wrong, inform user
        if random_quote is None:
            self.ui.log(f'Failed to get a quote from "{book.title}"')
            return

        self.ui.log(random_quote.text)
        self.quote_printed = True

        if not is_book_selected:
            if not delay_author:
                self._print_author_now(book, quotes_left_in_book)
            else:
                self._schedule_author_print(book, quotes_left_in_book, len(random_quote.text))

        # call counter update
        self.ui.update_quotes_ui_counter()

    def _print_author_now(
        self,
        book: Book,
        quotes_left_in_book: int,
        scroll_to_bottom: bool = True
    ) -> None:
        self.ui.log(f"\n{book.title}   / {quotes_left_in_book} left /", scroll_to_bottom)
        self.ui.log(f"{'-'*len(book.title)}", scroll_to_bottom)

    def _schedule_author_print(
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
            self.ui.cancel_timer(self.author_timer_id)

        # start the timer (id is like: "after#0", "after#1", etc.)
        # Type checker warning is incorrect — no extra arguments are needed here
        self.author_timer_id = self.ui.schedule(delay_ms, self._print_pending_author)

    def _print_pending_author(self) -> None:
        if self.pending_author_data:
            # unpack the stored tuple
            book, quotes_left_in_book = self.pending_author_data
            self._print_author_now(book, quotes_left_in_book, scroll_to_bottom=False)
        self.pending_author_data = None
        self.author_timer_id = None

    def _flush_pending_author(self, print_data: bool = True) -> None:
        if self.author_timer_id is not None:
            self.ui.cancel_timer(self.author_timer_id)
            self.author_timer_id = None
        if print_data and self.pending_author_data:
            book, quotes_left_in_book = self.pending_author_data
            self._print_author_now(book, quotes_left_in_book)
        self.pending_author_data = None

    def on_delay_author_toggle(self) -> None:
        checked = self.ui.delay_author_enabled()
        if not checked:
            if self.pending_author_data:
                self._flush_pending_author()
            else:
                # make already printed author visible
                self.ui.scroll_to_bottom()

    #=================================================
    # print every quote
    #=================================================
    def print_every_quote(self) -> None:
        # set back clear state
        self.ui.clear_text_output()
        self.ui.update_quotes_ui_counter(use_book_total=True)

        selected_title = self.ui.get_selected_book_title()
        if selected_title == constants.ANY_BOOK:
            self.ui.log("Select a book from the list.")
            return

        book = book_utils.get_book_by_title(self.ui.get_collection_books(), selected_title)
        if book is None:
            self.ui.log("Book not found.")
            return

        # book exists, get quotes for printing
        quotes = book_utils.get_quotes_sorted_by_page(book)
        self.ui.log(book.title)
        self.ui.log('-' * len(book.title))

        # setup async iteration state and start the loop
        self.book_quote_count = len(quotes)

        # enumerate(quotes) produces an iterator of (index, quote) pairs
        self.quote_iter = enumerate(quotes)
        self._print_next_quote()

    def _print_next_quote(self) -> None:
        try:
            i, quote = next(self.quote_iter)
        except StopIteration:
            # finished
            self.ui.scroll_to_top()
            self.ui.set_quotes_ui_counter(0)
            return

        header = f"{i + 1} / {self.book_quote_count}  (p.{quote.page})"
        self.ui.log(header)
        self.ui.log(quote.text)
        if i < (self.book_quote_count - 1):
            self.ui.log("\n")
        self.ui.set_quotes_ui_counter(self.book_quote_count - i)

        # schedule next iteration
        self.ui.schedule(5, self._print_next_quote)

    #=================================================
    # reset state
    #=================================================
    def reset_state(self) -> None:
        self._flush_pending_author(print_data=False)
        self.quote_printed = False
        self.book_header_printed = False
