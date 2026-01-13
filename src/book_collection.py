#=================================================
# IMPORT
#=================================================
from constants_loader import constants
import datetime
import json
import random
import re
import sys
 
#=================================================
# CLASSES
#=================================================
class Quote:
    def __init__(self, text, page_number):
        self.text = text
        self.page = page_number

    #=================================================
    # string representation
    #=================================================
    def __repr__(self):
        return f"Quote(text={self.text}, page_number={self.page})"

class Book:
    def __init__(self, title):
        self.title = title
        self.author = ""
        self.folder = ""
        self.file_id = ""
        self.annotation = ""
        self.pages_count = 0
        self.published_date = 0
        self.file_modified_date = 0
        self.have_read_date = 0
        self.activity_time = 0
        self.q_per_page = 0.0
        self.quotes = []
        self.short_quotes = []
        self.selected_set = set()
        self.first_q_timestamp = 0
        self.last_q_timestamp = 0
        self.rating = 0.0
        self.ratings_count = 0.0

    def add_quote(self, text, page_number, is_long=False):
        quote = Quote(text, page_number)
        if is_long:
            self.quotes.append(quote)
        else:
            self.short_quotes.append(quote)

    def get_all_quotes_list(self):
        return self.quotes + self.short_quotes

    def get_random_q(self):
        all_q = self.get_all_quotes_list()
        return self._rnd_q(all_q)

    def get_random_short_q(self):
        return self._rnd_q(self.short_quotes)

    def _rnd_q(self, quotes_list):
        quotes_left = 0
        random_quote = None
        unselected_quotes = [q for q in quotes_list if q not in self.selected_set]
        if unselected_quotes:
            random_quote = random.choice(unselected_quotes)
            self.selected_set.add(random_quote)
            quotes_left = len(unselected_quotes) - 1
        return random_quote, quotes_left

    def clear_selected_set(self):
        self.selected_set.clear()

    #=================================================
    # @property decorator is used to define a method
    # that can be accessed like an attribute
    #=================================================
    @property
    def total_q(self):
        return (len(self.quotes) + len(self.short_quotes))

    @property
    def total_short_q(self):
        return len(self.short_quotes)

    @property
    def has_remaining_quotes(self):
        return len(self.selected_set) < self.total_q

    @property
    def has_remaining_short_quotes(self):
        return any(q not in self.selected_set for q in self.short_quotes)

    #=================================================
    # string representation
    #=================================================
    def __repr__(self):
        return f"Book(title={self.title}, quotes={len(self.quotes)})"


#=================================================
# GLOBALS
#=================================================
# The Collection will be a simple list containing the Book instances
The_Collection = []
Folders = {}
All_Quotes_Count = 0
Short_Quotes_Count = 0

#=================================================
# FUNCTION: build The Collection
#=================================================
def build_the_collection():
    # return value
    error = None
    
    # these are in the global scope, indicate global to be able to modify
    global The_Collection
    global All_Quotes_Count
    global Short_Quotes_Count

    # reset globals
    The_Collection = []
    All_Quotes_Count = 0
    Short_Quotes_Count = 0

    # open and read the JSON file
    try:
        with open('library.json', 'r', encoding="utf8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        return error

    # get the folders dictionary, each value will be a set of book IDs
    for coll in data['colls']:
        Folders[coll['data']['coll_title']] = set(coll['docs'])

    for doc in data['docs']:
        if doc['data']['doc_active'] == 1:
            # Use regex to remove non-alphabet characters from the beginning of the title
            book_title = re.sub(r"^[^a-zA-Z]+", "", doc['data']['doc_file_name_title'])

            # handle renamed books, book_title is the default return
            book_title = constants.BOOK_RENAME_DICTIONARY.get(book_title, book_title)
            # remove funny character (Zero Width Space)
            book_title = book_title.replace('\u200b', '').strip()

            # add the book to The Collection (which is a list of instances)
            this_book = Book(book_title)
            The_Collection.append(this_book)

            # store additional data
            this_book.file_id = doc['uri']
            this_book.author = doc['data'].get('user_authors') or doc['data'].get('doc_authors')
            this_book.annotation = doc['data'].get('doc_annotation', "")

            # store file date as a date object, activity time as a simple timestamp
            aux_date = datetime.datetime.fromtimestamp(doc['data'].get('file_modified_time') / 1000)
            this_book.file_modified_date = aux_date
            this_book.activity_time = doc['data'].get('doc_activity_time')

            # get the folder, if available
            if Folders:
                for folder, ids in Folders.items():
                    if this_book.file_id in ids:
                        this_book.folder = folder
                        break

            # get pages count if available
            try:
                doc_data = json.loads(doc['data']['doc_position'])
                this_book.pages_count = doc_data['pagesCount']
            except (KeyError, ValueError, IndexError, TypeError, AttributeError):
                this_book.pages_count = 0

            # get goodreads data if available
            try:
                review_note = doc['reviews'][0]['note_body']
                this_book.published_date = int(review_note.split(';')[0].strip())
                this_book.rating = float(review_note.split(';')[1].strip())
                this_book.ratings_count = float(review_note.split(';')[2].strip().replace('k', '.'))
            except (KeyError, ValueError, IndexError, TypeError, AttributeError):
                this_book.published_date = 0
                this_book.rating = 0.0
                this_book.ratings_count = 0.0

            # get the citations
            if len(doc['citations']) > 0:
                quote_dates = []
                for citation in doc['citations']:
                    q_is_long = len(citation['note_body']) > constants.MAX_CHAR_IN_SHORT_QUOTE
                    this_book.add_quote(citation['note_body'], citation['note_page'], q_is_long)
                    quote_dates.append(citation['note_insert_time'])

                # sort the dates list to easily access first and last, convert to seconds
                quote_dates.sort()
                this_book.first_q_timestamp = quote_dates[0] / 1000
                this_book.last_q_timestamp = quote_dates[-1] / 1000

                # calculate the q/p ratio, avoid division by zero
                if this_book.pages_count > 0:
                    this_book.q_per_page = this_book.total_q / this_book.pages_count

            # check if current doc was finished or not
            read_at_timestamp = doc['data'].get('doc_have_read_time') / 1000
            if doc['data'].get('doc_have_read_time') != 0:
                if this_book.title in constants.EXCEPTION_TITLES_FOR_READ_DATE:
                    aux_date = datetime.datetime.fromtimestamp(constants.EXCEPTION_DATE_FOR_READ_DATE)
                elif ((this_book.last_q_timestamp - this_book.first_q_timestamp) > constants.ONE_DAY_IN_SECONDS and
                       this_book.title not in constants.EXCLUDED_TITLES_FROM_READ_DATE ):
                    # sanity check for doc have read time
                    if (read_at_timestamp - this_book.last_q_timestamp) < constants.MAX_SEC_BETWEEN_LAST_QUOTE_AND_READ_DATE:
                        aux_date = datetime.datetime.fromtimestamp(read_at_timestamp)
                    else:
                        aux_date = datetime.datetime.fromtimestamp(this_book.last_q_timestamp)
                else:
                    # use default date
                   # 2026-01-01 12:00:00
                    aux_date = datetime.datetime.fromtimestamp(1767265200)
            else:
                aux_date = datetime.datetime.fromtimestamp(0)

            # add the constructed date
            this_book.have_read_date = aux_date

    # gather titles, authors and quote counts
    for book in The_Collection:
        All_Quotes_Count += book.total_q
        Short_Quotes_Count += book.total_short_q

    # alphabetical order by title
    The_Collection.sort(key=lambda book: book.title)

    return error
