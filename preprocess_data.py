import os
from preprocess.pdf2text import text_cleaner
from preprocess.text2data import get_tokens_and_phrases, get_wordscore, rake_keywords, yake_keywords
from preprocess.data2table import create_ngram_table, get_ngram_table, create_keywords_table
import spacy
import pandas as pd
from csv import writer
import json
from yake import KeywordExtractor
import string
from tqdm import tqdm


if __name__ == '__main__':
    raw_data_path = 'data/raw_text/'
    processed_data_path = 'data/processed_text/'

    stops = set(line.strip() for line in open('data/functionalities/stopwords/stopwords.txt', "r", encoding='utf-8'))

    metadata_table = pd.read_csv(r'data/tables/metadata_table.csv', delimiter=',' ,index_col="dkey")

    nlp = spacy.load('models/Spacy_lg/', exclude=["parser","attribute_ruler", "ner"])
    nlp.enable_pipe('morphologizer')
    nlp.enable_pipe('tagger')
    nlp.enable_pipe('senter')

    nlp.Defaults.stop_words |= stops

    language = "pl"
    max_ngram_size = 3
    deduplication_threshold = 0.96
    deduplication_algo = 'seqm'
    window_size = 2
    numOfKeywords = 25

    custom_kw_extractor = KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold,
                                           dedupFunc=deduplication_algo, windowsSize=window_size, top=numOfKeywords,
                                           features=None, stopwords=stops)

    # keyword possible tags
    keyword_tags = ["SUBST", "ADJ", "XXX", "ADJA", "ADJC", "ADJP", "DEPR", "FIN",
    "INF", "IMPS"]

    pos_tags = ["INTERP", "BREV", "_SP"]

    ngram_table_path = 'data/tables/ngram_table.csv'
    rake_table_path = 'data/tables/rake_keywords_table.csv'
    yake_table_path = 'data/tables/yake_keywords_table.csv'

    if not os.path.exists(ngram_table_path):
        create_ngram_table().to_csv(ngram_table_path, encoding='utf-8-sig')

    if not os.path.exists(rake_table_path):
        create_keywords_table().to_csv(rake_table_path, encoding='utf-8-sig')

    if not os.path.exists(yake_table_path):
        create_keywords_table().to_csv(yake_table_path, encoding='utf-8-sig')

    row_num=len(metadata_table.index)+1
    for dkey in tqdm(metadata_table.index, total=row_num):

        with open(raw_data_path+dkey+'.txt', 'r', encoding="utf-8-sig") as document:
            raw_text = document.read()

            text = text_cleaner(raw_text)
            nlp_text = text.translate(str.maketrans('', '', string.digits))
            nlp.max_length = len(nlp_text) + 100
            spacy_text = nlp(nlp_text)

            tokens, phrases, un_ratio = get_tokens_and_phrases(spacy_text,min_length=3, max_phrase_length=4,
                                                     pos_tags=pos_tags, keyword_tags=keyword_tags)

            if len(tokens) < 100 or len(phrases) < 20 or un_ratio > 0.4:
                open('data_logs/error_logs/token_error_logs.txt', "a", encoding='utf-8-sig').write(dkey + '\n')
                continue

            with open(processed_data_path+dkey+'.json', 'w', encoding='utf-8-sig') as f:
                json.dump(tokens, f)

            # Get rake keywords:
            wordscores = get_wordscore(phrases, min_freq=2)
            rake_keys = rake_keywords(phrases, wordscores, numOfKeywords)
            with open(rake_table_path, 'a+', newline='', encoding='utf-8-sig') as write_obj:
                # Create a writer object from csv module
                csv_writer = writer(write_obj)
                # Add contents of list as last row in the csv file
                for elem in rake_keys:
                    csv_writer.writerow([dkey, elem[0], elem[0].count(' ') + 1, elem[1]])

            # Get yake keywords

            yake_keys = custom_kw_extractor.extract_keywords(text)
            with open(yake_table_path, 'a+', newline='', encoding='utf-8-sig') as write_obj:
                # Create a writer object from csv module
                csv_writer = writer(write_obj)
                # Add contents of list as last row in the csv file
                for elem in yake_keys:
                    csv_writer.writerow([dkey, elem[0], elem[0].count(' ') + 1, elem[1]])

            # Get ngrams
            preprocessed_text = [i[1] for i in tokens]
            ngram_table = get_ngram_table(preprocessed_text, n=5)
            with open(ngram_table_path, 'a+', newline='', encoding='utf-8-sig') as write_obj:
                # Create a writer object from csv module
                csv_writer = writer(write_obj)
                # Add contents of list as last row in the csv file
                for elem in ngram_table:
                    csv_writer.writerow([dkey, elem[0], elem[1], elem[2]])


