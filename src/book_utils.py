#=================================================
# IMPORT
#=================================================
import random
import re

from book_collection import Book, Quote
from constants_loader import constants
from typing import TypedDict

#=================================================
# helper
#=================================================
def find_book_by_title(collection: list[Book], title: str) -> Book | None:
    """
    Return the book instance with the given title from the collection.
    """
    return next((book for book in collection if book.title == title), None)

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
        book: Book | None = find_book_by_title(collection, selected_title)

        if book is None:
            return None, "Book not found."

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
# search functions
#=================================================
class SearchMatches(TypedDict):
    titles: set[str]
    quotes: dict[str, list[str]]

def search_books(books: list[Book], query: str) -> SearchMatches:

    # initialize the search results
    matches: SearchMatches = {
        "titles": set(),
        "quotes": {}
    }

    query = query.strip().lower()

    if not query:
        return matches

    for book in books:
        if query in book.title.lower():
            matches["titles"].add(book.title)

        for quote in book.quotes:
            if query in quote.text.lower():
                matches["quotes"].setdefault(book.title, []).append(quote.text)

    return matches

def add_blank_line(output: list[str], n: int = 1) -> None:
    for _ in range(n):
        output.append("")

def format_search_results_text(
    matches: SearchMatches,
    query: str = "",
    highlight_match: bool = False,
    show_headers: bool = True
) -> str:

    output: list[str] = []

    if highlight_match and not query:
        raise ValueError("query is required when highlight_match is True")

    # nothing found
    if not (matches["titles"] or matches["quotes"]):
        return "No match found."

    # title matches
    if show_headers and matches["titles"]:
        header = "Title matches"
        output.append(header)
        output.append("-" * len(header))
        add_blank_line(output)

        for title in sorted(matches["titles"]):
            output.append(title)

        # add spacing between sections
        if matches["quotes"]:
            add_blank_line(output, 3)

    # quote matches
    if matches["quotes"]:

        if show_headers:
            header = "Quote matches"
            output.append(header)
            output.append("-" * len(header))
            add_blank_line(output)
            
        # compile a case-insensitive regex pattern for the literal query text
        pattern = re.compile(re.escape(query), re.IGNORECASE) if query else None

        for i, (book_title, quotes) in enumerate(matches["quotes"].items()):
            if show_headers:
                output.append(book_title)
                output.append("-" * len(book_title))

            for j, q in enumerate(quotes):
                # highlight matches if enabled
                if pattern and highlight_match:
                    q = pattern.sub(query.upper(), q)

                output.append(q)
                # don't add double-spacing after last quote
                if j != len(matches["quotes"][book_title]) - 1:
                    add_blank_line(output, 2)

            if i != len(matches["quotes"]) - 1:
                add_blank_line(output, 3)

    return "\n".join(output)

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
