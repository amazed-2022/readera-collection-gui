#=================================================
# IMPORT
#=================================================
import re

from collections import Counter
from constants_loader import constants
from dataclasses import dataclass

#=================================================
# CLASSES
#=================================================
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


@dataclass
class WordStatistics:
    top_words: list[tuple[str, int]]
    book_word_counts: dict[str, Counter]
    top_book_for_word: dict[str, tuple[str, int]]

    @classmethod
    def from_collection(cls, collection, omit_words: list[str], top_n: int = 30):

        omit_set = set(omit_words)

        book_word_counts: dict[str, Counter] = {}
        top_book_for_word = {}
        global_counter = Counter()

        # per-book + global word frequency build
        for book in collection.books:
            # combine all quotes (long + short) into lowercase
            text = ' '.join(q.text for q in book.get_all_quotes_list()).lower()

            # generator of filtered words for Counter
            words = (
                w for w in re.findall(r"\b\w{4,}\b", text)
                if w not in omit_set
            )

            # build per-book frequency counter (word -> count) and store it
            counter = Counter(words)
            book_word_counts[book.title] = counter

            # accumulate into global word frequency counter
            global_counter.update(counter)
            
        # top words globally
        top_words = global_counter.most_common(top_n)
        
        # compute top book for word (only for top words, avoids full vocabulary scan)
        for word, _count in top_words:
            max_count = 0
            best_book = ""
            
            # scan all books' word counts
            for book_name, counter in book_word_counts.items():
                count = counter.get(word, 0)
                if count > max_count:
                    max_count = count
                    best_book = book_name
            
            # store (best book, count) for this word
            top_book_for_word[word] = (best_book, max_count)

        return cls(
            top_words=top_words,
            book_word_counts=book_word_counts,
            top_book_for_word=top_book_for_word
        )