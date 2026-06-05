#=================================================
# IMPORT
#=================================================
import datetime
import os
import random
import re
import sys
import textwrap
import unicodedata

from book_collection import BookCollection, Book
from book_statistics import Statistics, StatisticsReporter
from constants_loader import constants
from typing import Optional

#=================================================
# GLOBALS, CONSTANTS
#=================================================
# options order can be varied here, a dictionary will be built based
# on this list, with each option's list index as the key and the
# corresponding element from this list as the value (string)
OPTIONS = [
    "Random / All Quotes",
    "Random / Selected Author",
    "Random / Selected Folder",
    "Book / every quote",
    "Book / quote distribution",
    "Book / list by property",
    "Statistics",
    "Search",
    "Exit"
]

LENGTHS = ["Any length", "Short only"]

LENGTH_TO_METHOD = {
    "Any length": "get_random_q",
    "Short only": "get_random_short_q"
}

#=================================================
# FUNCTIONS
#=================================================
def create_options_menu(opt_lst: list[str]) -> dict[str, str]:
    options = {}
    for i, element in enumerate(opt_lst, start=1):
        if element != "Exit":
            options[str(i)] = element
        else:
            options['x'] = element
    return options

#=================================================
# get terminal width
#=================================================
def get_terminal_columns() -> int:
    """
    Return the current column size of the terminal window.
    """
    try:
        return os.get_terminal_size().columns
    except OSError:
        # Fallback to a default column size
        return 90

#=================================================
# print separator using hyphens
#=================================================
def print_separator_line() -> None:
    print('-' * get_terminal_columns(), end='')

#=================================================
# print options menu
#=================================================
def print_options() -> None:
    for key, value in Options_Menu.items():
        if key.isdigit():
            print(f" {int(key)}  -->  {value}")
        else:
            print(f" {key}  -->  {value}")

#=================================================
# get option
#=================================================
def get_option() -> str:
    prompts = [
        " Choice is the act of hesitation.. ",
        " ..that we make before making a decision. ",
        " It is a mental wobble. ",
        " And so we are always in a dither of doubt.. ",
        " ..as to whether we are behaving the right way.. ",
        " ..or doing the right thing, and so on and so forth... ",
        " It's time to choose an option.. ",
        " I'll wait a little longer...",
        " Running out of patience...",
        " Choose soon, or I'll exit.",
        " Tick tock... exit is approaching.",
        " Make a choice, or I'll choose goodbye.",
        " Warning: automatic exit imminent.",
        " Final countdown has started.",
        " Choose now, or I'll exit."
        ]

    header = "Choose an option:"
    print(f"{header}\n{'-' * len(header)}")
    print_options()
    print_separator_line()

    attempt  = 0
    while attempt  < len(prompts):
        opt = input(prompts[attempt ])

        if opt.isdigit() and opt in Options_Menu:
            return Options_Menu.get(opt, "Something went wrong")
        elif opt == 'x':
            sys.exit()
        attempt  += 1

    print("\n" + r" I told you so. ¯\_(°_o)/¯")
    sys.exit()

#=================================================
# FUNCTION: print random quotes
#=================================================
def print_random_quotes(
    books_for_print: list[Book],
    method: str,
    print_title: bool = True,
) -> None:
    while True:
        # random book for every iteration (or same book for a single-element list)
        book = random.choice(books_for_print)
        random_quote, quotes_left = getattr(book, method)()

        # get random returns None if there is no more quote left in that book
        if random_quote:
            print_wrapped_text(random_quote.text)

            # "delay" title print, but exit immediately if requested
            if is_exit_requested():
                return

            # print the "delayed" title if needed
            if print_title:
                print(f"{book.title}   / {quotes_left} left /")
                print(f"{'-' * len(book.title)}")
                if is_exit_requested():
                    return

            # separate printed title from the next quote
            print('\n')
        else:
            # refresh the list if no more quote is in the book
            books_for_print.remove(book)

        if not books_for_print:
            input("All quotes were printed.")
            return

#=================================================
# check exit request ('x')
#=================================================
def is_exit_requested() -> bool:
    response = input()
    return bool(response and response[0] == 'x')

#=================================================
# print wrapped text
#=================================================
def print_wrapped_text(text: str) -> None:
    print(*textwrap.wrap(f"{text}\n", get_terminal_columns() - 1), sep='\n')

#=================================================
# print items with selection numbers
#=================================================
def print_selection_list(items: list[str]) -> None:
    for idx, item in enumerate(items):
        print(f"{idx + 1:2d}.  -->  {item}")

#=================================================
# print items with selection numbers
#=================================================
def get_user_choice(
    input_type: str,
    max_value: int,
    zero_is_valid: bool = False,
    extra_prompt: str = "",
) -> int:
    min_value = 0 if zero_is_valid else 1
    article = ' a' if input_type != 'quote length' else ''
    n_suffix = 'n' if input_type == 'author' else ''
    prompt = f"\nChoose{article}{n_suffix} {input_type}{extra_prompt}: "

    while True:
        user_input = input(prompt)

        if user_input.isdigit():
            number = int(user_input)
            if min_value <= number <= max_value:
                return number

            print("You should choose more wisely.")
            continue

        # only allow "special escape" cases here-
        if input_type in {"folder", "quote length"} and not user_input:
            return 0

        print("This is not a valid number..")

#=================================================
# user can choose a book from the printed list
#=================================================
def choose_a_book(attr: str) -> Book:
    print(" 0.  -->  random book")

    if attr == "with_annotation":
        books_for_selection = [book for book in collection.books if book.annotation]
    else:
        books_for_selection = [book for book in collection.books if book.total_quotes > 0]

    titles = [book.title for book in books_for_selection]
    print_selection_list(titles)
    choice = get_user_choice("book", len(books_for_selection), zero_is_valid=True)
    print_separator_line()
    return books_for_selection[choice - 1] if choice else random.choice(books_for_selection)

#=================================================
# user can choose an author
#=================================================
def choose_an_author(authors: list[str]) -> str:
    print_selection_list(authors)
    choice = get_user_choice("author", len(authors))
    print_separator_line()
    return authors[choice - 1]

#=================================================
# user can choose a property
#=================================================
def choose_a_property() -> str:

    properties = [
        "added on",
        "reading now",
        "finished list",
        "read duration",
        "number of quotes",
        "quote/page ratio",
        "publish date",
        "rating",
        "folder",
        ]

    print_selection_list(properties)
    choice = get_user_choice("property", len(properties))
    print_separator_line()
    return properties[choice - 1]

#=================================================
# user can choose a folder
#=================================================
def choose_a_folder(
    folders: dict[str, set],
    allow_select_all: bool = True,
) -> Optional[str]:
    def strip_accents(s: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) != 'Mn'
        )

    folders_list = sorted(
        folders,
        key=lambda s: strip_accents(s).lower()
    )

    print_selection_list(folders_list)

    choice = get_user_choice(
        "folder",
        len(folders_list),
        extra_prompt=" (or press Enter to list all)" if allow_select_all else ""
    )
    print_separator_line()
    return folders_list[choice - 1] if choice else None

#=================================================
# user can choose between quote lengths
#=================================================
def choose_quote_length() -> str:
    print_selection_list(LENGTHS)
    choice = get_user_choice("quote length", len(LENGTHS))
    print_separator_line()
    return LENGTHS[choice - 1] if choice else LENGTHS[0]


#=================================================
# MAIN
#=================================================
collection = BookCollection()
error = collection.build_the_collection()

if error:
    print(error)
    sys.exit()

Options_Menu = create_options_menu(OPTIONS)
#=================================================
# main loop for printing
#=================================================
while True:
    # start with empty window
    os.system('cls')

    # print the main title and options
    string = f"== The Collection =="
    separator = '=' * len(string)
    print(f"{separator}\n{string}\n{separator}\n")

    # get option also prints the options menu
    option = get_option()
    print_separator_line()

    #=================================================
    # random quotes
    #=================================================
    if (option == "Random / All Quotes" or
        option == "Random / Selected Author" or
        option == "Random / Selected Folder"):

        # start with full list (all quotes)
        books = [book for book in collection.books if book.total_quotes > 0]

        # narrow down list if necessary
        if option == "Random / Selected Author":
            selected_author = choose_an_author(collection.authors_with_quotes)
            books = [b for b in books if b.author == selected_author]

        elif option == "Random / Selected Folder":
            selected_folder = (
                choose_a_folder(
                    collection.folders,
                    allow_select_all=False
                )
                if collection.folders
                else None
            )
            if selected_folder is not None:
                books = [b for b in books if b.folder == selected_folder]

        length = choose_quote_length()
        print_random_quotes(books, LENGTH_TO_METHOD[length])

    #=================================================
    # selected book section
    #=================================================
    elif (option == "Book / every quote" or
          option == "Book / quote distribution"):

        # get a book from the printed list
        selected_book = choose_a_book("with_quotes")

        #=================================================
        # all quotes in page order
        #=================================================
        if option == "Book / every quote":
            # open output file with context manager
            with open(f"{selected_book.title}.txt", "w", encoding="utf8") as f_output:
                # create a list sorted by page number of all quotes in the book
                sorted_by_page = sorted(selected_book.get_all_quotes_list(), key=lambda q: q.page)

                print(selected_book.title)
                print('-' * len(selected_book.title))
                f_output.write(f"{selected_book.title}\n")
                f_output.write(f"{'-' * len(selected_book.title)}\n")

                for i, quote in enumerate(sorted_by_page):
                    string = f"{i + 1} / {len(sorted_by_page)}  (p.{str(quote.page)})"
                    print(string)
                    print_wrapped_text(quote.text)
                    print()
                    f_output.write(f"{string}\n")
                    f_output.write(f"{quote.text}\n\n")

        #=================================================
        # quote distribution
        #=================================================
        elif option == "Book / quote distribution":
            print(f"{selected_book.title}\n{'-' * len(selected_book.title)}\n")

            # use terminal width as the base of the diagram size
            space = "    "
            columns = get_terminal_columns() - 10
            rows = round(columns * 0.2)
            res = selected_book.pages_count / columns

            # collect the distribution of quotes based on calculated resolution
            # use length of each quote instead of simply just the numbers
            q_distr = []
            for i in range(columns):
                q_distr.append(0)
                start_page = res * i
                end_page = res * (i + 1)
                for quote in selected_book.get_all_quotes_list():
                    if (quote.page > start_page) and (quote.page <= end_page):
                        q_distr[i] += len(quote.text)

            # map the distribution from (0) to (rows)
            old_min, old_max = min(q_distr), max(q_distr)
            new_min, new_max = 0, rows
            mapped_distr = [(new_max - new_min) * (x - old_min) / (old_max - old_min) + new_min for x in q_distr]

            print(f"{space}↑")
            # range is exclusive of the end value, but it's not a problem that rows number
            # will not be reached, because in this way, compare value (new max - i) will
            # not reach zero, so a row full of '*' character will not be printed
            for i in range(rows):
                row_str_list = []
                for j in range(columns):
                    row_str_list.append('*' if mapped_distr[j] >= (new_max - i) else ' ')

                # print the updated row immediately
                print(f"{space}|{''.join(row_str_list)}")

            print(f"{space}{'-' * columns}→")
            print(f"{space}1{' ' * (columns - len(str(selected_book.pages_count)) + 1)}{selected_book.pages_count}")

    #=================================================
    # generate book list by chosen property
    #=================================================
    elif option == "Book / list by property":

        book_property = choose_a_property()

        if book_property == "added on":
            sorted_books = sorted(collection.books, key=lambda book: book.file_modified_date, reverse=True)
        elif book_property == "reading now":
            sorted_books = sorted(collection.books, key=lambda book: book.published_date, reverse=True)
        elif book_property == "finished list":
            sorted_books = sorted(collection.books, key=lambda book: book.have_read_date, reverse=True)
        elif book_property == "read duration":
            sorted_books = sorted(collection.books, key=lambda book: book.first_q_timestamp, reverse=True)
        elif book_property == "publish date":
            sorted_books = sorted(collection.books, key=lambda book: book.published_date, reverse=True)
        elif book_property == "number of quotes":
            sorted_books = sorted(collection.books, key=lambda book: book.total_quotes, reverse=True)
        elif book_property == "quote/page ratio":
            sorted_books = sorted(collection.books, key=lambda book: book.quotes_per_page, reverse=True)
        elif book_property == "rating":
            sorted_books = sorted(collection.books, key=lambda book: book.rating, reverse=True)
        else:
            sorted_books = sorted(collection.books, key=lambda book: book.title, reverse=False)

        # choose function returns none if all is requested
        not_an_exception = book_property not in {"read duration", "reading now", "finished list"}
        folder = choose_a_folder(collection.folders) if (collection.folders and not_an_exception) else None

        while True:
            for book in sorted_books:
                if not folder or book.folder == folder:
                    # print book data according to chosen property
                    if book_property == "added on":
                        print(f"  -->  {book.file_modified_date.strftime('%Y-%b-%d')}  /  {book.title}")

                    elif book_property in {"reading now", "continued_as_reading_now"}:
                        if (book.activity_time != 0) and not book.is_read:
                            print(f"  -->  "
                                  f"{book.published_date:4d}  /  "
                                  f"{book.rating:.2f}  /  "
                                  f"{book.ratings_count:>{6}}k  /  "
                                  f"{book.pages_count:4d} pages  /  "
                                  f"{book.title}")

                    elif book_property in {"finished list", "continued_as_publish_date_of_finished"}:
                        if book.is_read:
                            if book_property == "finished list":
                                print(f"  -->  {book.have_read_date.strftime('%Y-%b-%d')}  /  {book.title}")
                            else:
                                print(f"  -->  {book.published_date}  /  {book.title}")

                    elif book_property == "read duration":
                        if ( book.first_q_timestamp > constants.START_DATE_FOR_READ_LIST and
                            (book.last_q_timestamp - book.first_q_timestamp) > constants.ONE_DAY_IN_SECONDS and
                             book.title not in constants.EXCLUDED_TITLES_FROM_READ_DURATION and
                             book.is_read):
                            dt_first = datetime.datetime.fromtimestamp(book.first_q_timestamp)
                            elapsed_days = (book.have_read_date - dt_first).days + 1
                            if dt_first.year == book.have_read_date.year:
                                dt_string = f"{dt_first.strftime('%Y %b.%d')} - {book.have_read_date.strftime('%b.%d')}"
                            else:
                                dt_string = f"{dt_first.strftime('%Y %b.%d')} - {book.have_read_date.strftime('%Y %b.%d')}"

                            print(f"  -->  {dt_string}{' ' * (25-len(dt_string))}  /  "
                                  f"{book.title}{' ' * (62-len(book.title))}"
                                  f"/ {book.pages_count:4d} pages  /  {int((book.pages_count / elapsed_days)+0.5):2d} / day")

                    elif book_property == "publish date":
                        date_data = f"{book.published_date:4d}" if book.published_date else " N/A"
                        pages_count = f"{book.pages_count:4d}" if book.pages_count else " N/A"
                        print(f"  -->  {date_data}  /  {pages_count} pages  /  {book.title}")

                    elif book_property == "number of quotes":
                        if book.total_quotes > 0:
                            print(f"  -->  {book.total_quotes:3d}  /  {book.title}")

                    elif book_property == "quote/page ratio":
                        if book.quotes_per_page > 0.0:
                            string = f"  -->  {book.quotes_per_page:.3f}  /  {book.title}"
                            print(f"{string}{' ' * (85-len(string))} ( {book.total_quotes:3d} / {book.pages_count:4d} )")

                    elif book_property in {"rating", "continued_as_ratings_count"}:
                        print(f"  -->  {book.rating:.2f}  /  {book.ratings_count:>{6}}k  /  {book.title}")

                    elif book_property == "folder":
                        date_data = f"{book.published_date:4d}" if book.published_date else " N/A"
                        pages_count = f"{book.pages_count:4d}" if book.pages_count else " N/A"
                        print(f"  -->  {date_data}  /  {pages_count} pages  /  {book.title}")

            if book_property not in {"reading now", "finished list", "rating"}:
                break
            else:
                # rating and finished lists are special
                print_separator_line()
                input()
                if book_property == "reading now":
                    sorted_books = sorted(collection.books, key=lambda book: book.ratings_count, reverse=True)
                    book_property = "continued_as_reading_now"
                elif book_property == "finished list":
                    # print based on ratings count
                    sorted_books = sorted(collection.books, key=lambda book: book.published_date, reverse=True)
                    book_property = "continued_as_publish_date_of_finished"
                elif book_property == "rating":
                    # print based on ratings count in the second round
                    sorted_books = sorted(collection.books, key=lambda book: book.ratings_count, reverse=True)
                    book_property = "continued_as_ratings_count"
                else:
                    break

        print_separator_line()

    #=================================================
    # statistics
    #=================================================
    elif option == "Statistics":
        stats = Statistics.from_collection(collection)
        reporter = StatisticsReporter(print)
        reporter.report(
            stats=stats,
            collection=collection,
            max_short_quote_chars=constants.MAX_CHAR_IN_SHORT_QUOTE,
            omitted_words=constants.WORDS_TO_OMIT_FROM_SEARCH,
            top_n_words=30
        )

    #=================================================
    # search
    #=================================================
    elif option == "Search":
        while True:
            search_prompt = "Search for at least 3 characters: "
            str_to_search = input(search_prompt).lower()
            print('-' * (len(search_prompt) + len(str_to_search)))

            if len(str_to_search) >= 3:
                counter = 0
                for book in collection.books:
                    match_in_book = False

                    for quote in book.get_all_quotes_list():
                        quote_text = quote.text.lower()

                        if str_to_search in quote_text:

                            # check if it's the first match in this book
                            if not match_in_book:
                                print_separator_line()
                                print(f"{book.title}\n{'-' * len(book.title)}\n")
                                match_in_book = True

                            # print the quote with the search term highlighted
                            print_wrapped_text(quote.text.replace(str_to_search, str_to_search.upper()))
                            print('\n')

                            # use findall, because a quote may contain the searched word multiple times
                            counter += len(re.findall(str_to_search, quote_text))

                result = f"Matched {counter} time{'s' if counter > 1 else ''}."
                print(result if counter else "No match found.")
                print('-' * len(result) if counter else '')

            elif str_to_search == 'x':
                break
            else:
                print("Incorrect input.")
            print('\n')
            print_separator_line()

    #=================================================
    # error
    #=================================================
    elif option == "Something went wrong":
        print("Error.")

    #=================================================
    # hold on and clear screen before next iteration
    #=================================================
    if (option != "Random / All Quotes"        and
        option != "Random / Short Quotes"      and
        option != "Random / Selected Author"   and
        option != "Random / Selected Folder"   and
        option != "Search"):
        input()

    # start over with next iteration
    for book in collection.books:
        book.clear_selected_set()

    os.system('cls')
