import pandas as pd
from typing import Union
from preprocess.text2data import get_ngrams


def create_metadata_table() -> pd.DataFrame:
    # Create metadata table
    # Contains:
    # dkey: string - document key (md5 hash of document)
    # doc_title: string - document title from filename
    # title: string - document title from document metadata
    # authors: string - list of authors from document metadata
    # source: string - source of document from document metadata
    # keywords: string - list of keywords from document metadata

    metadata_table = pd.DataFrame(columns=['dkey', 'title', 'authors', 'source', 'type', 'keywords', 'url'])
    metadata_table.set_index('dkey', inplace=True)
    return metadata_table


def create_ngram_table() -> pd.DataFrame:
    ngram_table = pd.DataFrame(columns=['dkey', 'ngram', 'ngram_tokens', 'term_freq'])
    ngram_table.set_index('dkey', inplace=True)
    return ngram_table


def create_keywords_table() -> pd.DataFrame:
    keyword_table = pd.DataFrame(columns=['dkey', 'keywords', 'keywords_tokens', 'keyword_score'])
    keyword_table.set_index('dkey', inplace=True)
    return keyword_table


def add_to_meta_table(dkey: str, metadata: Union[dict, tuple], url: str, doc_type: str = ' ') -> None:
    # Add data to metadata table
    # Input:
    # metadata_table: pd.dataframe - metadata table to append data
    # filename: str - document filename
    # dkey: string - document key (md5 hash of document)
    # metadata: dict - metadata of file
    metadata_table = pd.DataFrame(columns=['dkey', 'title', 'authors', 'source', 'type', 'keywords', 'url'])

    if type(metadata) is dict:
        try:
            title = metadata['title']
        except:
            title = ' '

        try:
            authors = metadata['author']
        except:
            authors = ' '

        try:
            source = metadata['subject']
        except:
            source = ' '

        try:
            keywords = metadata['keywords']
        except:
            keywords = ' '

        metadata_table.loc[dkey] = title, authors, source, doc_type, keywords, url

    elif type(metadata) is tuple:
        title = metadata[0]
        authors = metadata[1]
        source = metadata[2]
        doc_type = metadata[3]
        keywords = metadata[4]

        metadata_table.loc[dkey] = title, authors, source, doc_type, keywords, url


def get_ngram_table(data: Union[str, dict], len_vec: list = [], n: int = 5) -> pd.DataFrame:
    # Create pandas dataframe containing key of document, ngrams (1 to n), their corresponding length and number of
    # occurrences in text
    # Input:
    # dkey: string - key of document (name)
    # data: string|dict - if string - extract n grams and corresponding data, else use dict of ngrams and occurances
    # len_vec: list - list of ngrams corresponding lengths
    # n: int - number of ngrams to extract (only if data is string)
    # Output:
    # pandas dataframe containing:
    # dkey [str]: document key
    # ngram [tuple(str)]: ngrams (unigrams, bigrams, trigrams, ..., n-grams)
    # ngram_tokens [int]: number of tokens (words) in the ngram (e.g., unigrams: 1, bigrams: 2)
    # term_freq [float]: frequency of occurrences of the ngram in the document

    if type(data) is list:
        grams, len_vec = get_ngrams(data, n)
    else:
        grams = data

    ngram = list(grams.keys())
    ngram_tokens = len_vec
    term_freq = list(grams.values())
    sum_tf = sum(term_freq)
    term_freq[:] = [x / sum_tf for x in term_freq]

    return list(zip(ngram, ngram_tokens, term_freq))
