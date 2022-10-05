from nltk import ngrams
from nltk.probability import FreqDist
from typing import Union
import spacy
from collections import defaultdict
from more_itertools import take
from yake import KeywordExtractor


def get_ngrams(text: list[str], n: int) -> (dict, list):
    # get ngrams for n in range (1-n)
    # Input:
    # text - user defined tokens
    # n - upper bound of n-grams size n
    # Output:
    # (dict of ngrams and number of their occurrences in text, list of corresponding length of ngrams)
    # eg. test sentence one -> for n=2 -> ((test, sentence), num_of_occurrences   [2,
    #                                     (sentence, one),  num_of_occurrences),  2]

    nngrams = FreqDist()

    for i in range(n):
        for s in ngrams(text, n=i + 1):
            nngrams[s] += 1

    ngram_len_vec = []
    for key in nngrams.keys():
        ngram_len_vec.append(len(key))

    return nngrams, ngram_len_vec


def get_tokens_and_phrases(text: spacy.tokens.doc.Doc, min_length: int = 0, max_phrase_length=5, pos_tags: list[str] = ["INTERP"], keyword_tags=[]):
    # remove stopwords from custom tokenized text or spacy document class
    # Input:
    # text: spacy.tokens.doc.Doc - spacy doc class
    # min_length: int - minimum length of word to leave in text default=0
    # pos_tags: list[str] - list of POS Tags from spacy pipeline to remove (only for spacy class with tagger)
    # Output:
    # clean_text: list[str] - list of tokens
    # phrases: list[str] - list of phrases
    # un_ratio: float - unknown to all words ratio

    clean_tokens = []
    phrases = []
    unknown_tokens = 0
    all_tokens = 0
    phrase = []
    ii = 0

    for token in text:
        ii = ii+1
        if not token.is_stop and len(token.lemma_) > min_length and token.tag_ not in pos_tags and len(token.text) < 20:
            clean_tokens.append((token.text, token.lemma_, token.tag_))
            all_tokens += 1
            if token.tag_ == "XXX":
                unknown_tokens += 1

        if token.is_stop or token.tag_ not in keyword_tags or len(token) < 3 or len(token.text) > 20:
            if phrase:
                if len(phrase) < max_phrase_length:
                    phrases.append(phrase)
                phrase = []
        else:
            phrase.append(token.lemma_)

    try:
        un_ratio = unknown_tokens/all_tokens
    except ZeroDivisionError:
        un_ratio = 1
    return clean_tokens, phrases, un_ratio


def get_wordscore(phrases: list[str], min_freq: int = 1) -> dict:
    # TODO - description

    frequency = defaultdict(int)
    degree = defaultdict(int)
    word_score = defaultdict(float)

    vocabulary = []

    for phrase in phrases:
        for word in phrase:
            frequency[word] += 1
            degree[word] += len(phrase)
            if word not in vocabulary:
                vocabulary.append(word)

    for word in vocabulary:
        if frequency[word] > min_freq:
            word_score[word] = (degree[word]) / (frequency[word])
        else:
            word_score[word] = 0

    return word_score


def rake_keywords(phrases: list[str], word_score: dict, num: int = 10):
    # Get keywords from phrases using rake algorithm
    # Input:
    # Output:
    # TODO - description

    keywords = defaultdict(float)
    for phrase in phrases:
        key = ' '.join(phrase)
        for word in phrase:
            keywords[key] = keywords.get(key, 0) + word_score[word]

    keywords = dict(sorted(keywords.items(), key=lambda item: item[1], reverse=True))

    return take(num, keywords.items())


def yake_keywords(text: str, num: int = 10, max_ngram_size: int = 5, stopwords=None):
    # Get keywords using YAKE

    language = "pl"
    max_ngram_size = max_ngram_size
    deduplication_threshold = 0.9
    deduplication_algo = 'seqm'
    window_size = 1
    numOfKeywords = num

    custom_kw_extractor = KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold,
                                           dedupFunc=deduplication_algo, windowsSize=window_size, top=numOfKeywords,
                                           features=None, stopwords= stopwords)

    return custom_kw_extractor.extract_keywords(text)

