# TF-IDF
from os import walk
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
import json
import joblib
import pandas as pd
from tqdm import tqdm
from preprocess.data2table import create_ngram_table
import os
from csv import writer

# TODO - descriptions
def sort_coo(coo_matrix):
    tuples = zip(coo_matrix.col, coo_matrix.data)
    return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)


def extract_topn_from_vector(feature_names, sorted_items, topn=10):
    """get the feature names and tf-idf score of top n items"""

    # use only topn items from vector
    sorted_items = sorted_items[:topn]
    score_vals = []
    feature_vals = []

    # word index and corresponding tf-idf score
    for idx, score in sorted_items:
        # keep track of feature name and its corresponding score
        score_vals.append(round(score, 3))
        feature_vals.append(feature_names[idx])
    # create a tuples of feature,score
    # results = zip(feature_vals,score_vals)
    results = {}
    for idx in range(len(feature_vals)):
        results[feature_vals[idx]] = score_vals[idx]

    return results

# TF-IDF
def read_text_only(path):
    text = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
        for i in data:
            text.append(i[1])
    return text


class CleanText:

    def __init__(self, path, filename):
        self.path = path
        self.filename = filename
        self.dkey = filename[:-5]

    def read(self):
        text = []
        with open(self.path+self.filename, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            for i in data:
                text.append(i[1])
        return text


def dummy(x):
    return x

def get_vectorizer():

    directory_path = "data/processed_text/"
    filenames = next(walk(directory_path), (None, None, []))[2]  # [] if no file
    texts = []

    for filename in filenames:
        texts.append(CleanText(directory_path,filename))


    vectorizer = CountVectorizer(max_df=0.7, tokenizer=dummy, preprocessor=dummy, stop_words=None,
                                 ngram_range=(1, 3), encoding='utf-8-sig', input='file')

    wcv = vectorizer.fit_transform(texts)


    tfidf_transformer = TfidfTransformer(smooth_idf=True, use_idf=True)
    tfidf_transformer.fit(wcv)
    joblib.dump(tfidf_transformer,
                "models/CountVectorizer/" + "vectorizer_" + str(1) + str(3) + "_0" + str(int(0.7 * 10)) + ".pkl")
    joblib.dump(tfidf_transformer, "models/CountVectorizer/" + "tfidf_" + str(1) + str(3) + "_0" + str(int(0.7 * 10)) + ".pkl")

def get_keywords(doc_dir, doc_name, tfidf, cv, feature_names):
    doc = CleanText(doc_dir, doc_name)
    doct = cv.transform([doc])
    tfidf_vec = tfidf.transform(doct)
    sorted_items = sort_coo(tfidf_vec.tocoo())
    keywords = extract_topn_from_vector(feature_names, sorted_items, 25)
    return keywords
    #print(keywords)


if __name__ == '__main__':
    # using sklearn - CountVectorizer create a vocabulary of words from directory of texts
    tfidf = joblib.load('models/CountVectorizer/tfidf_12_07.pkl')
    cv = joblib.load('models/CountVectorizer/vectorizer_12_07.pkl')
    feature_names = cv.get_feature_names()

    metadata_table = pd.read_csv(r'data/tables/metadata_table.csv', delimiter=',' ,index_col="dkey")
    tfidf_table_path = 'data/tables/tfidf_keywords_table.csv'

    if not os.path.exists(tfidf_table_path):
        create_ngram_table().to_csv(tfidf_table_path, encoding='utf-8-sig')

    row_num = len(metadata_table.index) + 1
    for dkey in tqdm(metadata_table.index, total=row_num):
        try:
            keywords = get_keywords('data/processed_text/', dkey+'.json',  tfidf, cv, feature_names)
        except FileNotFoundError:
            continue

        with open(tfidf_table_path, 'a+', newline='', encoding='utf-8-sig') as write_obj:
            # Create a writer object from csv module
            csv_writer = writer(write_obj)
            # Add contents of list as last row in the csv file
            for key, value in keywords.items():
                csv_writer.writerow([dkey, key, key.count(' ') + 1, value])