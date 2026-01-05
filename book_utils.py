#=================================================
# IMPORT
#=================================================
import constants
import datetime
import random


#=================================================
# functions for print_random_quote
#=================================================
def get_book_for_random_quote(collection, selected_title, filtered_titles, length="any"):
    """
    Return a valid book for random quote selection or None.
    Also returns a message if no book/quote is available.
    """
    if selected_title == constants.ANY_BOOK:
        # build books list with available quotes
        books = [
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
        book = get_book_by_title(collection, selected_title)
        
        # check for available quote(s)
        if length != "short":
            if not book.has_remaining_quotes:
                return None, "All quotes were printed."
        elif not book.has_remaining_short_quotes:
            return None, "No (more) short quotes available in the selected book."
        
        # book is valid for random quote
        return book, None

def get_random_quote(book, length="any"):
    """
    Return (quote, remaining_count).
    """
    if length != "short":
        return book.get_random_q()
    return book.get_random_short_q()



#=================================================
# functions for print_every_quote
#=================================================
def get_book_by_title(collection, title):
    """
    Return the book with the given title from the collection.
    """
    return next((book for book in collection if book.title == title), None)

def get_quotes_sorted_by_page(book):
    """
    Return all quotes from a book sorted by page number.
    """
    return sorted(book.get_all_quotes_list(), key=lambda q: q.page)

def get_and_export_quotes(book, filename):
    """
    Return and export all quotes from a book to a text file.
    """
    quotes = get_quotes_sorted_by_page(book)

    with open(filename, "w", encoding="utf8") as f:
        f.write(f"{book.title}\n")
        f.write(f"{'-' * len(book.title)}\n")

        for i, quote in enumerate(quotes):
            header = f"{i + 1} / {len(quotes)}  (p.{quote.page})"
            f.write(f"{header}\n{quote.text}\n\n")

    return quotes
    

#=================================================
# functions for print_quote_distribution
#=================================================
def compute_quote_distribution(book, columns=50, rows=10):
    """
    Compute a distribution of quote lengths over the book pages.
    Returns a list of mapped heights for each column.
    """
    # proportions
    res = book.pages_count / columns
    q_distr = [0] * columns
    quotes = book.get_all_quotes_list()

    # fill distribution
    for i in range(columns):
        start_page = res * i
        end_page = res * (i + 1)
        for quote in quotes:
            if start_page < quote.page <= end_page:
                q_distr[i] += len(quote.text)

    # map distribution to rows
    old_min, old_max = min(q_distr), max(q_distr)
    if old_max == old_min:
        mapped_distr = [0] * columns
    else:
        mapped_distr = [rows * (x - old_min) / (old_max - old_min) for x in q_distr]

    return mapped_distr
    
def calculate_columns_from_width(ctrl_width_px, avg_char_width, min_columns=30, ratio=0.94):
    usable_px = int(ctrl_width_px * ratio) - 20
    return max(min_columns, int(usable_px / avg_char_width) - 1)
    
    
#=================================================
# functions for print_list_by_property
#=================================================
def sort_books_for_property(books, book_property):
    """
    Return a sorted list of books based on the given property.
    """
    if book_property == constants.PROP_ADDED_ON:
        return sorted(books, key=lambda b: b.file_modified_time, reverse=True)
    elif book_property == constants.PROP_READING_NOW:
        return sorted(books, key=lambda b: b.published_date, reverse=True)
    elif book_property == constants.PROP_FINISHED_LIST:
        return sorted(books, key=lambda b: b.have_read_time, reverse=True)
    elif book_property == constants.PROP_READ_DURATION:
        return sorted(books, key=lambda b: b.first_q_date, reverse=True)
    elif book_property == constants.PROP_PUBLISH_DATE:
        return sorted(books, key=lambda b: b.published_date, reverse=True)
    elif book_property == constants.PROP_NUMBER_OF_QUOTES:
        return sorted(books, key=lambda b: b.total_q, reverse=True)
    elif book_property == constants.PROP_Q_PER_PAGE_RATIO:
        return sorted(books, key=lambda b: b.q_per_page, reverse=True)
    elif book_property == constants.PROP_RATING:
        return sorted(books, key=lambda b: b.rating, reverse=True)
    elif book_property == constants.PROP_FOLDER:
        return sorted(books, key=lambda b: b.title, reverse=False)
    elif book_property == constants.PROP_RATINGS_COUNT:
        return sorted(books, key=lambda b: b.ratings_count, reverse=True)
    # fallback: return unsorted
    return books
    
def filter_books_by_folder(books, folder):
    if folder == constants.ANY_FOLDER:
        return books
    return [b for b in books if b.folder == folder]
    
def get_info_row_by_property(book, book_property, print_pages=False, require_finished=False):
    """
    Return a formatted string representing a book's info based on the given property.
    Returns None if the book should be skipped (e.g., filtered out).
    """
    if book_property == constants.PROP_ADDED_ON:
        return f"{book.file_modified_time.strftime('%Y-%b-%d')}  /  {book.title}"
    elif book_property == constants.PROP_READING_NOW:
        if (book.activity_time != 0) and (book.have_read_time.year == 1970):
            return (f"{book.published_date:4d}  /  "
                    f"{book.rating:.2f}  /  "
                    f"{book.ratings_count:>{6}}k  /  "
                    f"{book.pages_count:4d} pages  /  {book.title}")
        return None
    elif book_property == constants.PROP_FINISHED_LIST:
        if book.have_read_time.year > 1970:
            return f"{book.have_read_time.strftime('%Y-%b-%d')}  /  {book.title}"
        return None
    elif book_property == constants.PROP_READ_DURATION:
        if (book.first_q_date > constants.START_DATE_FOR_READ_LIST and
            (book.last_q_date - book.first_q_date) > constants.ONE_DAY_IN_SECONDS and
            book.title not in constants.EXCLUDED_TITLES_FROM_READ_DURATION and
            book.have_read_time.year > 1970):
            dt_first = datetime.datetime.fromtimestamp(book.first_q_date)
            elapsed_days = (book.have_read_time - dt_first).days + 1
            if dt_first.year == book.have_read_time.year:
                dt_string = f"{dt_first.strftime('%Y %b.%d')} - {book.have_read_time.strftime('%b.%d')}"
            else:
                dt_string = f"{dt_first.strftime('%Y %b.%d')} - {book.have_read_time.strftime('%Y %b.%d')}"
            return (f"{dt_string}{' ' * (25-len(dt_string))}  /  "
                    f"{book.title}{' ' * (62-len(book.title))}/ {book.pages_count:4d} pages  /  "
                    f"{int((book.pages_count / elapsed_days)+0.5):2d} / day")
        return None
    elif book_property == constants.PROP_PUBLISH_DATE:
        if require_finished and book.have_read_time.year <= 1970:
            return None
            
        date_data = f"{book.published_date:4d}" if book.published_date else " N/A"
        if print_pages:
            pages_text = f"{book.pages_count:4d} pages  /  " if book.pages_count else " N/A pages  /  "
        else:
            pages_text = ""
        return f"{date_data}  /  {pages_text}{book.title}"
    elif book_property == constants.PROP_NUMBER_OF_QUOTES:
        if book.total_q > 0:
            return f"{book.total_q:3d}  /  {book.title}"
        return None
    elif book_property == constants.PROP_Q_PER_PAGE_RATIO:
        if book.q_per_page > 0.0:
            clean_title = book.title.replace('\u200b', '').strip()
            string = f"{book.q_per_page:.3f}  /  {clean_title}"
            return f"{string}{' ' * (78-len(string))} ( {book.total_q:3d} / {book.pages_count:4d} )"
        return None
    elif book_property == constants.PROP_RATING:
        return f"{book.rating:.2f}  /  {book.ratings_count:>{6}}k  /  {book.title}"
    elif book_property == constants.PROP_FOLDER:
        # controlled delegation
        return get_info_row_by_property(book, constants.PROP_PUBLISH_DATE, print_pages=True)
    elif book_property == constants.PROP_RATINGS_COUNT:
        return f"{book.rating:.2f}  /  {book.ratings_count:>{6}}k  /  {book.title}"
    return None