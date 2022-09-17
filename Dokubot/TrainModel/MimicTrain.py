import tensorflow as tf
import spacy
import numpy as np
from sklearn.model_selection import train_test_split
import io
import json
import keras.backend as K


class MimicData():

    def __init__(self, max_word_length=25, chars_tokens=None, spacy_path = None,  spacy_size='lg'):
        self.max_word_len = max_word_length
        self.words_list = None
        self.vectors_list = None
        self.num_chars = None
        self.tokenized_chars = None
        self.num_of_samples = None
        self.embedding_dim = None
        self.X_train, self.X_test, self.y_train, self.y_test = None
        self.char_tokenizer = tf.keras.preprocessing.text.Tokenizer(num_words=chars_tokens, lower=False, filters=None, oov_token="OOV")
        self.load_spacy_embeddings(spacy_path=spacy_path, spacy_size=spacy_size)
        self.train_tokenizer(self.words_list, self.max_word_len)
        self.get_train_test_data()

    def load_spacy_embeddings(self, spacy_path = None, spacy_size = 'lg'):
        if spacy_path:
            nlp = spacy.load(spacy_path)
        else:
            if spacy_size == 'lg':
                nlp = spacy.load('pl_core_news_lg', disable=["attribute_ruler", "ner", 'tagger',
                                                                  'parser','morphologizer'])
            elif spacy_size == 'md':
                nlp = spacy.load('pl_core_news_md', disable=["attribute_ruler", "ner", 'tagger',
                                                                  'parser', 'morphologizer'])

        words_list_full = []
        vectors_list_full = []
        for key, vector in nlp.vocab.vectors.items():
            words_list_full.append(list(nlp.vocab.strings[key]))
            vectors_list_full.append(vector)

        self.words_list = words_list_full
        self.vectors_list = np.array(vectors_list_full)
        self.embedding_dim = self.vectors_list.shape[1]
        self.num_of_samples = self.vectors_list.shape[0]

    def train_tokenizer(self, words_list, max_word_len):
        self.char_tokenizer.fit_on_texts(words_list)
        mimic_data = self.char_tokenizer.texts_to_sequences(list(words_list))
        # Pad slot data
        mimic_data_padded = np.zeros([len(mimic_data), max_word_len])
        for i in range(len(mimic_data)):
            if len(mimic_data[i]) > max_word_len:
                mimic_data_padded[i, :] = mimic_data[i][0:max_word_len]
            else:
                mimic_data_padded[i, 0:len(mimic_data[i])] = mimic_data[i][:]

        #vocab = char_tokenizer.word_counts
        self.num_chars = len(self.char_tokenizer.word_index) + 1
        self.tokenized_chars = mimic_data_padded.astype(np.int32)

    def get_train_test_data(self, test_size=0.2, random_state=7312):

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.tokenized_chars, self.vectors_list,
                                                            test_size=test_size, random_state=random_state)

    def save_tokenizer(self, path):
        tokenizer_json = self.char_tokenizer.to_json()
        with io.open(path+'char_tokenizer_'+str(self.num_chars)+'.json', 'w', encoding='utf-8-sig') as f:
            f.write(json.dumps(tokenizer_json, ensure_ascii=False))


def euclidean_distance_loss(y_true, y_pred):
    return K.sqrt(K.sum(K.square(y_true-y_pred), axis=-1, keepdims=True))


class MimicModel():
    def __init__(self, MimicData, loss_function='cos_sim'):

        if loss_function == 'cos_sim':
            self.loss = tf.keras.losses.CosineSimilarity(axis=1)
        elif loss_function == 'euc_dist':
            self.loss = euclidean_distance_loss

        self.optimizer = tf.keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-07, amsgrad=False, name="Adam")
        self.epochs = 50
        self.metrics = 'accuracy'
        self.bach_size = 128
        self.validation_split = 0.2

        self.max_word_length = MimicData.max_word_len
        self.embedding_dim = MimicData.embedding_dim
        self.num_chars = MimicData.num_chars
        ## Train test data

        ## MODEL
        self.model = None

        self.input = tf.keras.layers.Input(shape=(self.max_word_length), dtype="int32")
        self.mask = tf.keras.layers.Masking(mask_value=0)
        self.embedding = tf.keras.layers.Embedding(input_dim=self.num_chars, output_dim=128, input_length=self.max_word_length)

        self.BiLSTM = tf.keras.layers.Bidirectional(layer=tf.keras.layers.LSTM(units=164))
        self.dropout = tf.keras.layers.Dropout(0.1)
        self.dense = tf.keras.layers.Dense(units=400, activation='tanh')
        self.output = tf.keras.layers.Dense(self.embedding_dim, activation=None)

        self.training_history = None
        self.evaluation = None

    def compile_model(self):
        self.input = self.input
        self.mask = self.mask(self.input)
        self.emedding = self.embedding(self.mask)
        self.BiLSTM = self.BiLSTM(self.emedding)
        self.dense = self.dense(self.BiLSTM)
        self.dropout = self.dropout(self.dense)
        self.output = self.output(self.dropout)

        self.model = tf.keras.models.Model(self.input, self.output)
        self.model.compile(optimizer=self.optimizer, loss=self.loss, metrics=self.metrics)
        self.model.summary()

    def train_model(self, MimicData, size=None, evaluate=False):

        if not self.model:
            self.compile_model()

        X_train, X_test, y_train, y_test = MimicData.get_train_test_data()

        self.training_history = self.model.fit(x=X_train, y=y_train, batch_size=self.bach_size, epochs=self.epochs,
                                               validation_split=self.validation_split)

        if evaluate:
            self.evaluate_model(X_test, y_test)

    def evaluate_model(self, X_test, Y_test):
        self.evaluation = self.model.evaluate(x=X_test, y=Y_test)
