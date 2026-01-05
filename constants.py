#=================================================
# CONFIGURABLE CONSTANTS
#=================================================

#=================================================
# short quotes length limit
#=================================================
MAX_CHAR_IN_SHORT_QUOTE = 300

#=================================================
# read list can be started from a timestamp
#=================================================
# 2024-02-23 12:00:00
START_DATE_FOR_READ_LIST = 1708686000
# 2026-01-01 12:00:00
# START_DATE_FOR_READ_LIST = 1767265200

#=================================================
# books can be renamed (e.g. made shorter)
#=================================================
BOOK_RENAME_DICTIONARY = {
    "Adele Faber, Elaine Mazlish - Beszélj úgy, hogy érdekelje, hallgasd úgy, hogy elmesélje":
        "Adele Faber, Elaine Mazlish - Beszélj úgy, hogy érdekelje..",
    "Eckhart Tolle - The Power of Now2":
        "Eckhart Tolle - The Power of Now",
    "Dummy author - Dummy title":
        "Author - Title"
    }
    
# BOOK_RENAME_DICTIONARY = {
    # "Dummy Author - Dummy Title":
        # "Author - Title"
    # }

#=================================================
# exclude titles from read duration (interval)
#=================================================
EXCLUDED_TITLES_FROM_READ_DURATION = {
    "Máté Gábor - A test lázadása",
    "Dummy book"
    }

# EXCLUDED_TITLES_FROM_READ_DURATION = {
    # "Dummy Author - Dummy Title"
    # }
    
#=================================================
# exclude titles from finished book list
#=================================================
EXCLUDED_TITLES_FROM_READ_DATE = {
    "Máté Gábor - A test lázadása",
    "Michael A. Singer - Felszabadított lélek",
    "Milan Kundera - A jelentéktelenség ünnepe",
    "Viktor E. Frankl - ...mégis mondj Igent az Életre!",
    "Viktor E. Frankl - Az élet értelméről"
    }

# EXCLUDED_TITLES_FROM_READ_DATE = {
    # "Dummy Author - Dummy Title"
    # }
    
#=================================================
# exception can be added to alter finished date
#=================================================
# Friday, March 1, 2024 12:00:00 PM GMT+01:00
EXCEPTION_DATE_FOR_READ_DATE = 1709290800
EXCEPTION_TITLES_FOR_READ_DATE = {
    "Nick Trenton - Ne agyald túl!",
    "Tisha Morris - Rendterapia"
    }   

# 2026-01-01 12:00:00
# EXCEPTION_DATE_FOR_READ_DATE = 1767265200
# EXCEPTION_TITLES_FOR_READ_DATE = {
    # "Dummy Author - Dummy Title"
    # }
    
 
#=================================================
# omit words from search results
#=================================================
WORDS_TO_OMIT_FROM_SEARCH = [
    "hogy", "that", "your", "this", "their", "they", "with", "vagy", "have",
    "csak", "from", "what", "there", "will", "when", "kell", "which", "mint",
    "more", "minden", "only", "ember", "mert", "into", "because", "them",
    "akkor", "olyan", "most", "amikor", "amit", "cannot", "become", "other",
    "arra", "pedig", "make", "every", "then", "mindig", "than", "hanem",
    "volt", "these", "through", "even", "always", "about", "must", "lehet",
    "need", "very", "without", "such", "know", "things", "some", "nincs",
    "amely", "vagyunk", "something", "those", "lesz", "want", "others",
    "find", "nagy", "saját", "just", "ilyen", "becomes", "azonban", "őket",
    "nagyon", "számára", "azért", "valami", "annak", "ezek", "éppen", "tehát",
    "azzal", "magát", "aztán", "való", "hogyan"
    ]
    
# WORDS_TO_OMIT_FROM_SEARCH = [
    # "that", "your", "this", "their", "they", "with", "have",
    # "from", "what", "there", "will", "when", "which", "more",
    # "only", "into", "because", "them", "cannot", "become", "other",
    # "make", "every", "then", "than", "these", "through", "even",
    # "always", "about", "must", "need", "very", "without", "such",
    # "know", "things", "some", "something", "those", "want", "others",
    # "find", "just", "becomes"
    # ]
    
    
#=================================================
# CONSTANTS
#=================================================
GUI_TITLE = "The Collection"
ANY_FOLDER = "Any folder.."
ANY_AUTHOR = "Any author.."
ANY_BOOK = "Any book.."

PROP_ADDED_ON = "added on"
PROP_READING_NOW = "reading now"
PROP_FINISHED_LIST = "finished list"
PROP_READ_DURATION = "read duration"
PROP_PUBLISH_DATE = "publish date"
PROP_NUMBER_OF_QUOTES = "number of quotes"
PROP_Q_PER_PAGE_RATIO = "quote/page ratio"
PROP_RATING = "rating"
PROP_FOLDER = "folder"
PROP_RATINGS_COUNT = "ratings count"
PROP_PUBLISH_DATE_FOR_FINISHED

PROPERTIES = [
            PROP_ADDED_ON,
            PROP_READING_NOW,
            PROP_FINISHED_LIST,
            PROP_READ_DURATION,
            PROP_PUBLISH_DATE,
            PROP_NUMBER_OF_QUOTES,
            PROP_Q_PER_PAGE_RATIO,
            PROP_RATING,
            PROP_FOLDER
        ]
                
ONE_DAY_IN_SECONDS = 86400