#=================================================
# IMPORT
#=================================================
import re

from book_collection import BookCollection
from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable

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


class StatisticsReporter:

    def __init__(self, write, line_width=48):
        self.line_width = line_width
        # output callback provided at construction time (UI/CLI abstraction)
        self.emit: Callable[[str], Any] = write

    #=================================================
    # MAIN
    #=================================================
    def report(
        self,
        stats: Statistics,
        collection: BookCollection,
        max_short_quote_chars: int,
        omitted_words: list[str],
        top_n_words: int = 30

    ):
        #=================================================
        # books
        #=================================================
        self.emit(self.section("Statistics"))
        self.emit("")
        self.report_stat_line(
                "Books in The Collection",
                f"{stats.books_count:4d} / 100%"
            )

        if stats.books_21st:
            self.report_stat_line(
                "Books from the 21st century",
                f"{stats.books_21st:4d} / "
                f"{self.get_percentage_string(stats.books_21st, stats.books_count)}"
            )

        if stats.books_20th:
            self.report_stat_line(
                "Books from the 20th century",
                f"{stats.books_20th:4d} / "
                f"{self.get_percentage_string(stats.books_20th, stats.books_count)}"
            )

        self.report_stat_line(
            "Books with quotes",
            f"{stats.books_with_quotes:4d} / "
            f"{self.get_percentage_string(stats.books_with_quotes, stats.books_count)}"
        )

        self.report_stat_line(
            "Books finished",
            f"{stats.books_read:4d} / "
            f"{self.get_percentage_string(stats.books_read, stats.books_count)}",
            blank_line=True
        )

        # folders (book counts)
        self.report_folder_dict(stats.folder_book_counts, stats.books_count)

        #=================================================
        # quotes
        #=================================================
        self.report_stat_line(
            "Quotes in total",
            f"{stats.total_quotes_count:4d} / 100%"
        )

        self.report_stat_line(
            f"Quotes that are less than {max_short_quote_chars} characters",
            f"{stats.total_short_quotes_count:4d} / "
            f"{self.get_percentage_string(stats.total_short_quotes_count, stats.total_quotes_count)}"
        )

        avg = (
            round(stats.total_quotes_count / stats.books_with_quotes)
            if stats.books_with_quotes else 0
        )

        self.report_stat_line("Quotes per book on average", f"{avg:4d}", blank_line=True)
        self.report_folder_dict(stats.folder_quote_counts, stats.total_quotes_count)

        #=================================================
        # authors
        #=================================================
        self.emit(self.section("Top 15 Authors"))

        cumulative = 0
        for i, (author, count) in enumerate(stats.author_quotes.items(), start=1):
            cumulative += count
            self.report_stat_line(
                f" --> {author}",
                f"{count:4d} / {self.get_percentage_string(count, stats.total_quotes_count, digit=2)}"
                f" / {self.get_percentage_string(cumulative, stats.total_quotes_count, digit=2)}"
            )
            if i >= 15:
                break

        #=================================================
        # words
        #=================================================
        self.emit("\n")
        self.emit(self.section(f"Top {top_n_words} most used words"))

        word_stats = WordStatistics.from_collection(
            collection,
            omitted_words,
            top_n=top_n_words
        )

        for word, count in word_stats.top_words:
            # get the book with the most occurrence of the word
            book_string, max_count = word_stats.top_book_for_word[word]
            self.emit(
                f" --> {count:3d} x {word}"
                f"{' ' * (12 - len(word))}"
                f"{max_count:3d} / {book_string}"
            )

    #=================================================
    # HELPERS
    #=================================================
    def report_stat_line(self, string, value, blank_line=False):
        self.emit(f"{string}  {'-'*(self.line_width-len(string))}>  {value}")
        if blank_line:
            self.emit("")

    def report_folder_dict(self, folder_dict, total):
        for folder, count in folder_dict.items():
            self.report_stat_line(
                f" --> {folder}",
                f"{count:4d} / {self.get_percentage_string(count, total)}"
            )
        self.emit("\n")

    @staticmethod
    def section(title):
        return f"{title}\n{'-' * len(title)}"

    @staticmethod
    def get_percentage_string(count, total, digit=3):
        return f"{int((count/total)*100):{digit}d}%" if total else "0%"
