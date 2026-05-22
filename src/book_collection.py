#=================================================
# IMPORT
#=================================================
import json
import random
import re

from constants_loader import constants
from dataclasses import dataclass
from datetime import datetime

#=================================================
# CLASSES
#=================================================
class Quote:
    def __init__(self, text: str, page_number: int) -> None:
        self.text = text
        self.page = page_number

    #=================================================
    # string representation
    #=================================================
    def __repr__(self) -> str:
        return f"Quote(text={self.text}, page_number={self.page})"


class Book:
    def __init__(self, title: str) -> None:
        self.title = title
        self.author: str = ""
        self.folder: str = ""
        self.file_id: str = ""
        self.annotation: str = ""
        self.pages_count: int = 0
        self.published_date: int = 0
        self.file_modified_date: datetime = datetime.fromtimestamp(0)
        self.have_read_date: datetime = datetime.fromtimestamp(0)
        self.activity_time: int = 0
        self.quotes_per_page: float = 0.0
        self.quotes: list[Quote] = []
        self.short_quotes: list[Quote] = []
        self.selected_quotes_set: set[Quote] = set()
        self.first_q_timestamp: float = 0
        self.last_q_timestamp: float = 0
        self.rating: float = 0.0
        self.ratings_count: float = 0.0

    def add_quote(self, text: str, page_number: int, is_long: bool=False) -> None:
        quote: Quote = Quote(text, page_number)
        if is_long:
            self.quotes.append(quote)
        else:
            self.short_quotes.append(quote)

    def get_all_quotes_list(self) -> list[Quote]:
        return self.quotes + self.short_quotes

    def get_random_q(self) -> tuple[Quote | None, int]:
        all_q: list[Quote] = self.get_all_quotes_list()
        return self._rnd_q(all_q)

    def get_random_short_q(self) -> tuple[Quote | None, int]:
        return self._rnd_q(self.short_quotes)

    def _rnd_q(self, quotes_list: list[Quote]) -> tuple[Quote | None, int]:
        unselected_quotes: list[Quote] = [q for q in quotes_list if q not in self.selected_quotes_set]
        if not unselected_quotes:
            return None, 0
        random_quote: Quote = random.choice(unselected_quotes)
        self.selected_quotes_set.add(random_quote)
        return random_quote, len(unselected_quotes) - 1

    def clear_selected_set(self) -> None:
        self.selected_quotes_set.clear()

    #=================================================
    # @property decorator is used to define a method
    # that can be accessed like an attribute
    #=================================================
    @property
    def total_quotes(self) -> int:
        return len(self.quotes) + len(self.short_quotes)

    @property
    def total_short_quotes(self) -> int:
        return len(self.short_quotes)

    @property
    def has_remaining_quotes(self) -> bool:
        return self.remaining_quote_count > 0

    @property
    def has_remaining_short_quotes(self) -> bool:
        return any(q not in self.selected_quotes_set for q in self.short_quotes)

    @property
    def remaining_quote_count(self) -> int:
        return self.total_quotes - len(self.selected_quotes_set)

    @property
    def is_read(self) -> bool:
        return self.have_read_date.year > 1970

    #=================================================
    # string representation
    #=================================================
    def __repr__(self) -> str:
        return f"Book(title={self.title}, quotes={len(self.quotes)})"


class BookCollection:
    def __init__(self) -> None:
        # The Collection is stored as an instance attribute
        self.books: list[Book] = []
        self.folders: dict[str, set] = {}

    #=================================================
    # FUNCTION: build The Collection
    #=================================================
    def build_the_collection(self) -> Exception | None:
        # return value
        error: Exception | None = None

        # reset state
        self.books = []
        self.folders = {}

        # open and read the JSON file
        try:
            with open('library.json', 'r', encoding="utf8") as file:
                data: dict = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            return error

        # get the folders dictionary, each value will be a set of book IDs
        for coll in data['colls']:
            self.folders[coll['data']['coll_title']] = set(coll['docs'])

        for doc in data['docs']:
            if doc['data']['doc_active'] == 1:
                # Use regex to remove non-alphabet characters from the beginning of the title
                book_title: str = re.sub(r"^[^a-zA-Z]+", "", doc['data']['doc_file_name_title'])

                # handle renamed books, book_title is the default return
                book_title = constants.BOOK_RENAME_DICTIONARY.get(book_title, book_title)
                # remove funny character (Zero Width Space)
                book_title = book_title.replace('\u200b', '').strip()

                # add the book to The Collection (which is a list of instances)
                this_book: Book = Book(book_title)
                self.books.append(this_book)

                # store additional data
                this_book.file_id = doc['uri']
                this_book.author = doc['data'].get('user_authors') or doc['data'].get('doc_authors')
                this_book.annotation = doc['data'].get('doc_annotation', "")

                # store file date as a date object, activity time as a simple timestamp
                aux_date: datetime = datetime.fromtimestamp(doc['data'].get('file_modified_time') / 1000)
                this_book.file_modified_date = aux_date
                this_book.activity_time = doc['data'].get('doc_activity_time')

                # get the folder, if available
                if self.folders:
                    for folder, ids in self.folders.items():
                        if this_book.file_id in ids:
                            this_book.folder = folder
                            break

                # get pages count if available
                try:
                    doc_data: dict = json.loads(doc['data']['doc_position'])
                    this_book.pages_count = doc_data['pagesCount']
                except (KeyError, ValueError, IndexError, TypeError, AttributeError):
                    this_book.pages_count = 0

                # get goodreads data if available
                try:
                    review_note: str = doc['reviews'][0]['note_body']
                    this_book.published_date = int(review_note.split(';')[0].strip())
                    this_book.rating = float(review_note.split(';')[1].strip())
                    this_book.ratings_count = float(review_note.split(';')[2].strip().replace('k', '.'))
                except (KeyError, ValueError, IndexError, TypeError, AttributeError):
                    this_book.published_date = 0
                    this_book.rating = 0.0
                    this_book.ratings_count = 0.0

                # get the citations
                if len(doc['citations']) > 0:
                    quote_dates: list[int] = []
                    for citation in doc['citations']:
                        q_is_long: bool = len(citation['note_body']) > constants.MAX_CHAR_IN_SHORT_QUOTE
                        this_book.add_quote(citation['note_body'], citation['note_page'], q_is_long)
                        quote_dates.append(citation['note_insert_time'])

                    # sort the dates list to easily access first and last, convert to seconds
                    quote_dates.sort()
                    this_book.first_q_timestamp = quote_dates[0] / 1000
                    this_book.last_q_timestamp = quote_dates[-1] / 1000

                    # calculate the q/p ratio, avoid division by zero
                    if this_book.pages_count > 0:
                        this_book.quotes_per_page = round(this_book.total_quotes / this_book.pages_count, 2)

                # check if current doc was finished or not
                read_at_timestamp: float = doc['data'].get('doc_have_read_time') / 1000
                if doc['data'].get('doc_have_read_time') != 0:
                    if this_book.title in constants.EXCEPTION_TITLES_FOR_READ_DATE:
                        aux_date = datetime.fromtimestamp(constants.EXCEPTION_DATE_FOR_READ_DATE)
                    elif ((this_book.last_q_timestamp - this_book.first_q_timestamp) > constants.ONE_DAY_IN_SECONDS and
                        this_book.title not in constants.EXCLUDED_TITLES_FROM_READ_DATE ):
                        # sanity check for doc have read time
                        if (read_at_timestamp - this_book.last_q_timestamp) < constants.MAX_SEC_BETWEEN_LAST_QUOTE_AND_READ_DATE:
                            aux_date = datetime.fromtimestamp(read_at_timestamp)
                        else:
                            aux_date = datetime.fromtimestamp(this_book.last_q_timestamp)
                    else:
                        # use default date
                        aux_date = datetime.fromtimestamp(constants.DEFAULT_DATE_FOR_READ_DATE)
                else:
                    aux_date = datetime.fromtimestamp(0)

                # add the constructed date
                this_book.have_read_date = aux_date

        # alphabetical order by title
        self.books.sort(key=lambda bk: bk.title)
        return error


@dataclass
class Statistics:

    books_count: int
    books_20th: int
    books_21st: int
    books_with_quotes: int
    books_read: int

    total_quotes_count: int
    total_short_quotes_count: int

    author_quotes: dict[str, int]
    folder_quote_counts: dict[str, int]
    folder_book_counts: dict[str, int]

    @classmethod
    def from_collection(cls, collection):

        author_quotes = {}
        folder_quote_counts = {}
        folder_book_counts = {}

        books_with_quotes = 0
        books_read = 0

        total_quotes_count = 0
        total_short_quotes_count = 0

        books_20th = 0
        books_21st = 0

        for book in collection.books:
            if book.total_quotes > 0:
                books_with_quotes += 1
                # gather author based stats
                author_quotes[book.author] = (
                    author_quotes.get(book.author, 0)
                    + book.total_quotes
                )
            if book.is_read:
                books_read += 1
            if 1900 <= book.published_date < 2000:
                books_20th += 1
            if book.published_date >= 2000:
                books_21st += 1

            # gather folders stats
            folder_quote_counts[book.folder] = (
                folder_quote_counts.get(book.folder, 0)
                + book.total_quotes
            )

            folder_book_counts[book.folder] = (
                folder_book_counts.get(book.folder, 0)
                + 1
            )

            total_quotes_count += book.total_quotes
            total_short_quotes_count += book.total_short_quotes

        # sort dicts descending based on count
        author_quotes = dict(
            sorted(
                author_quotes.items(),
                key=lambda item: item[1],
                reverse=True
            )
        )

        folder_quote_counts = dict(
            sorted(
                folder_quote_counts.items(),
                key=lambda item: item[1],
                reverse=True
            )
        )

        folder_book_counts = dict(
            sorted(
                folder_book_counts.items(),
                key=lambda item: item[1],
                reverse=True
            )
        )

        return cls(
            books_count=len(collection.books),
            books_with_quotes=books_with_quotes,
            books_read=books_read,

            books_20th=books_20th,
            books_21st=books_21st,

            total_quotes_count=total_quotes_count,
            total_short_quotes_count=total_short_quotes_count,

            author_quotes=author_quotes,
            folder_quote_counts=folder_quote_counts,
            folder_book_counts=folder_book_counts,
        )
