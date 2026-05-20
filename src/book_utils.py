#=================================================
# IMPORT
#=================================================
import datetime
import random

from book_collection import Book, Quote
from constants_loader import constants

#=================================================
# functions for print_random_quote
#=================================================
def get_book_for_random_quote(
    collection: list[Book],
    selected_title: str,
    filtered_titles: list[str],
    length: str = "any"
) -> tuple[Book | None, str | None]:
    """
    Return a valid book for random quote selection or None.
    Also returns a message if no book/quote is available.
    """
    if selected_title == constants.ANY_BOOK:
        # build books list with available quotes
        books: list[Book] = [
            book
            for book in collection
            if book.title in filtered_titles
            and (book.has_remaining_quotes if length != "short" else book.has_remaining_short_quotes)
        ]

        # check if any book remains at all
        if books:
            return random.choice(books), None
        else:
            return None, "All quotes were printed."
    else:
        # get the selected book instance
        book: Book | None = get_book_by_title(collection, selected_title)

        # check for available quote(s)
        if length != "short":
            if not book.has_remaining_quotes:
                return None, "All quotes were printed."
        elif not book.has_remaining_short_quotes:
            return None, "No (more) short quotes available in the selected book."

        # book is valid for random quote
        return book, None


def get_random_quote(book: Book, length: str = "any") -> tuple[Quote | None, int]:
    """
    Return (quote, remaining_count).
    """
    if length != "short":
        return book.get_random_q()
    return book.get_random_short_q()


#=================================================
# functions for print_every_quote
#=================================================
def get_book_by_title(collection: list[Book], title: str) -> Book | None:
    """
    Return the book instance with the given title from the collection.
    """
    return next((book for book in collection if book.title == title), None)


def get_quotes_sorted_by_page(book: Book) -> list[Quote]:
    """
    Return all quotes from a book sorted by page number.
    """
    return sorted(book.get_all_quotes_list(), key=lambda q: q.page)


def get_and_export_quotes(book: Book, filename: str) -> list[Quote]:
    """
    Return and export all quotes from a book to a text file.
    """
    quotes: list[Quote] = get_quotes_sorted_by_page(book)

    if filename:
        with open(filename, "w", encoding="utf8") as f:
            f.write(f"{book.title}\n")
            f.write(f"{'-' * len(book.title)}\n")

            for i, quote in enumerate(quotes):
                header: str = f"{i + 1} / {len(quotes)}  (p.{quote.page})"
                f.write(f"{header}\n{quote.text}\n\n")

    return quotes


#=================================================
# functions for print_quote_distribution
#=================================================
def compute_quote_distribution(
    book: Book,
    columns: int = 50,
    rows: int = 10
) -> list:
    """
    Compute a distribution of quote lengths over the book pages.
    Returns a list of mapped heights for each column.
    """
    # proportions
    res: float = book.pages_count / columns
    q_distr: list[int] = [0] * columns
    quotes: list = book.get_all_quotes_list()

    # fill distribution
    for i in range(columns):
        start_page: float = res * i
        end_page: float = res * (i + 1)
        for quote in quotes:
            if start_page < quote.page <= end_page:
                q_distr[i] += len(quote.text)

    # map distribution to rows
    old_min: int = min(q_distr)
    old_max: int = max(q_distr)
    if old_max == old_min:
        mapped_distr: list[int] = [0] * columns
    else:
        mapped_distr = [
            rows * (x - old_min) / (old_max - old_min)
            for x in q_distr
        ]

    return mapped_distr


def calculate_columns_from_width(
    ctrl_width_px: int,
    avg_char_width: int,
    min_columns: int = 30,
    ratio: float = 0.94
) -> int:
    usable_px: int = int(ctrl_width_px * ratio) - 20
    return max(min_columns, int(usable_px / avg_char_width) - 1)
