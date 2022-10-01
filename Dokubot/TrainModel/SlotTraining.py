import numpy as np
import tensorflow as tf
import pandas as pd
import spacy
import statistics
from sklearn.model_selection import train_test_split
import json

def pad_array(word, length):
    word_padded = np.zeros([1, length]).astype(np.int32)
    if len(word[0]) > length:
        word_padded[0][:] = word[0][0:length]
    else:
        word_padded[0][0:len(word[0])] = word[0]
    return word_padded


class Mimic(object):

    @classmethod
    def load(cls, mimic_path, tokenizer_path):
        mimic_model = tf.keras.models.load_model(mimic_path,
                                                 custom_objects = {'euclidean_distance': cls.euclidean_distance})
        with open(tokenizer_path, encoding='utf-8-sig') as f:
            data = json.load(f)
        char_tokenizer = tf.keras.preprocessing.text.tokenizer_from_json(data)
        return cls(mimic_model, char_tokenizer)

    def euclidean_distance(cls, y_true, y_pred):
        return K.sqrt(K.sum(K.square(y_true - y_pred), axis=-1, keepdims=True))

    def __init__(self, mimic_model, char_tokenizer):
        self._mimic_model = mimic_model
        self._char_tokenizer = char_tokenizer
        self.max_word_len = self._mimic_model.layers[0].output_shape[0][1]

    def __call__(self, doc):
        for token in doc:
            if token.is_oov:
                word_tokenized = self._char_tokenizer.texts_to_sequences([token.chars])
                token.chars_tokens = pad_array(word_tokenized, self.max_word_len)
                token.vector = self._mimic_model.predict(token.chars_tokens,verbose=0).reshape((-1,))
        #return doc

    def predict_from_word(self, word):
        chars = list(word)
        word_tokenized = self._char_tokenizer.texts_to_sequences([chars])
        word_padded = pad_array(word_tokenized, self.max_word_len)
        vector = self._mimic_model.predict(word_padded, verbose=0)
        return vector


class SlotData():
    def __init__(self, question_path, mimic_path, tokenizer_path, max_sentence_length=30, spacy_path = None, spacy_size='lg', OOV_initial='mean',):
        if OOV_initial == 'mimic':
          self.mimic = Mimic.load(mimic_path, tokenizer_path)
        self.spacy_path = spacy_path
        self.spacy_size = spacy_size
        self.max_sentence_length = max_sentence_length
        self.slot_data = self.prepare_pd(question_path)
        self.data_len = None
        self.embedding_dimention = 300

        self.complete_tokenization_accuracy = None
        self.token_accuracy = None

        # load spacy model
        if self.spacy_path:
            self.nlp = spacy.load(spacy_path)
        else:
            if spacy_size == 'lg':
                self.nlp = spacy.load('pl_core_news_lg', disable=["attribute_ruler", "ner", 'tagger',
                                                                  'parser','morphologizer'])
            elif spacy_size == 'md':
                self.nlp = spacy.load('pl_core_news_md', disable=["attribute_ruler", "ner", 'tagger',
                                                                  'parser', 'morphologizer'])
            elif spacy_size == 'sm':
                self.nlp = spacy.load('pl_core_news_sm', exclude=["attribute_ruler", "ner", 'tagger',
                                                                  'parser', 'morphologizer'])
        self.X_data = None
        self.Y_data = None

        self.vocab = None
        self.slot_types_number = None
        self.prepare_slot_data(OOV_initial=OOV_initial)
        self.prepare_slot_tokenizer()
        self.print_token_accuracy()

    def prepare_pd(self, path):
        slot_data = pd.read_csv(path, index_col=0)
        slot_data['tokens_list'] = slot_data['tokens'].apply(eval)
        slot_data['slots_list'] = slot_data['slots'].apply(eval)
        slot_data.drop_duplicates(subset=['sentence'])
        self.data_len = slot_data.shape[0]
        #print(slot_data.head())
        return slot_data

    def prepare_slot_data(self, drop_bad_tokenization=True, OOV_initial = 'mean'):
        token_accuracy_list = []
        complete_tokenization_accuracy = []
        spacy_tokenization = []
        sentence_vectors = []
        curr = 0
        lennnl = len(self.slot_data.index)
        for index, sentence in self.slot_data.iterrows():
            if curr % 200 == 0:
              print(curr, "/", lennnl)
            curr += 1
            spacy_text = self.nlp(sentence['sentence'])
            spacy_tokens = [token.text for token in spacy_text]
            sentence_tokens = sentence['tokens_list']
            spacy_tokenization.append(spacy_tokens)

            word_vectors = np.zeros([self.max_sentence_length, self.embedding_dimention])
            i = 0
            if spacy_tokens == sentence_tokens:
                complete_tokenization_accuracy.append(1)
                for token in spacy_text:
                    if i == self.max_sentence_length:
                        break

                    if not token.is_oov:
                        word_vectors[i, :] = token.vector.tolist()
                    else:
                        if OOV_initial == 'random':
                            word_vectors[i, :] = np.random.rand(1,self.embedding_dimention) *1

                        elif OOV_initial == 'mimic':
                            word_vectors[i, :] = self.mimic.predict_from_word(token.text)[0]
                            #print(token.text,word_vectors[i, :])
                        elif OOV_initial == 'none':
                           word_vectors[i, :] = np.ones([1,self.embedding_dimention])

                    i = i + 1
            else:
                #print(spacy_tokens)
                #print(sentence_tokens)

                complete_tokenization_accuracy.append(0)

            sentence_vectors.append(word_vectors)

            token_accuracy = 0
            for index in range(len(sentence_tokens)):
                try:
                    if sentence_tokens[index] == spacy_tokens[index]:
                        token_accuracy += 1
                except IndexError:
                    break

            token_accuracy_list.append(token_accuracy / len(sentence_tokens))

        self.complete_tokenization_accuracy = statistics.mean(complete_tokenization_accuracy)
        self.token_accuracy = statistics.mean(token_accuracy_list)
        self.slot_data['spacy_tokens'] = spacy_tokenization
        self.slot_data['tokens_same'] = complete_tokenization_accuracy
        self.slot_data['word_vectors'] = sentence_vectors

        if drop_bad_tokenization:
            self.slot_data = self.slot_data[self.slot_data['tokens_same'] == 1]

        self.X_data = np.array([np.array(i) for i in self.slot_data['word_vectors']])
        self.Y_data = self.slot_data['slots_list']

    def prepare_slot_tokenizer(self):
        slot_list = self.Y_data
        slot_tokenizer = tf.keras.preprocessing.text.Tokenizer(lower=True)
        slot_tokenizer.fit_on_texts(list(slot_list))
        Y_data = slot_tokenizer.texts_to_sequences(list(slot_list))
        # Pad slot data
        Y_data_padded = np.zeros([len(Y_data), self.max_sentence_length])
        for i in range(len(Y_data)):
            if len(Y_data[i]) > self.max_sentence_length:
                Y_data_padded[i, :] = Y_data[i][0:self.max_sentence_length]
            else:
                Y_data_padded[i, 0:len(Y_data[i])] = Y_data[i][:]

        self.Y_data = Y_data_padded
        self.vocab = slot_tokenizer.word_index.items()
        self.slot_types_number = len(self.vocab)+1

    def print_token_accuracy(self):
        print('Complete accuracy: ', self.complete_tokenization_accuracy)
        print('Token accuracy: ', self.token_accuracy)

    def get_train_test_data(self):
        test_size = 0.2
        random_state = 7312

        # Split the dataset into train and test
        X_train, X_test, y_train, y_test = train_test_split(self.X_data, self.Y_data,
                                                            test_size=test_size, random_state=random_state)
        y_train = tf.keras.utils.to_categorical(y_train)
        y_test = tf.keras.utils.to_categorical(y_test)

        return X_train, X_test, y_train, y_test


if __name__ == '__main__':

    train_data_table = pd.DataFrame(columns=['tokens', 'vectors', 'slots'])
    train_data_table.to_csv(encoding='utf-8-sig')

    sot_data = SlotData("/content/drive/MyDrive/Dokubot/Questions/dokubot_slot_questions18.csv",
                        '/content/drive/MyDrive/Dokubot/mimic/mimic_medium/mimic_super_smol.h5',
                        "/content/drive/MyDrive/Dokubot/char_tokenizer_md.json",
                        OOV_initial='mimic', spacy_size='sm')

    X_train, X_test, y_train, y_test = sot_data.get_train_test_data()
