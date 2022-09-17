import numpy as np
import tensorflow as tf
import pandas as pd
import spacy
import statistics
from LoadModels import Mimic
from sklearn.model_selection import train_test_split

class SlotData():
    def __init__(self, question_path, mimic_path, tokenizer_path, max_sentence_length=30, spacy_path = None, spacy_size='lg', OOV_initial='mean',):
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
        return slot_data

    def prepare_slot_data(self, drop_bad_tokenization=True, OOV_initial = 'mean'):
        token_accuracy_list = []
        complete_tokenization_accuracy = []
        spacy_tokenization = []
        sentence_vectors = []
        for index, sentence in self.slot_data.iterrows():
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
                        if OOV_initial == 'mean':
                            word_vectors[i, :] = np.mean(word_vectors[0:i, :], axis=0)
                        elif OOV_initial == 'mimic':
                            word_vectors[i, :] = self.mimic.predict_from_word(token.text)[0]

                    i = i + 1
            else:
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
        slot_tokenizer = tf.keras.preprocessing.text.Tokenizer(lower=False)
        slot_tokenizer.fit_on_texts(list(slot_list))
        Y_data = slot_tokenizer.texts_to_sequences(list(slot_list ))
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
    sot_data = SlotData("/data/questions/dokubot_slot_data4.csv",
                        'C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/models/Mimic/mimic.h5',
                        "C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/models/Char_tokenizer/char_tokenizer_992.json",
                        spacy_path="C:/Users/Bennu/Desktop/Praca magisterska/Dokubot/models/Spacy_lg/")


    X_train, X_test, y_train, y_test = sot_data.get_train_test_data()

    # Set training parameters
    loss = tf.keras.losses.CategoricalCrossentropy()
    metrics = [tf.keras.metrics.Precision(), tf.keras.metrics.Recall(), 'accuracy']
    epochs = 10
    optimizer = tf.keras.optimizers.Adam(
        learning_rate=0.0001,
        beta_1=0.9,
        beta_2=0.999,
        epsilon=1e-07,
        amsgrad=False,
        name="Adam"
    )
    denselayer = tf.keras.layers.Dense(8, activation='softmax')

    ### MODEL CREATION ###
    # Input for word vectors
    input = tf.keras.Input(shape=(30, 300), dtype="float32")

    # Next, we add a masking layer to innform model that some part of the data is
    # actually a padding and should be ignored

    mask = tf.keras.layers.Masking(mask_value=0.)(input)
    BiLSTM = tf.keras.layers.Bidirectional(
        layer=tf.keras.layers.LSTM(
            units=124,
            activation="relu",
            recurrent_activation="tanh",
            use_bias=True,
            kernel_initializer="glorot_uniform",
            recurrent_initializer="orthogonal",
            bias_initializer="zeros",
            unit_forget_bias=True,
            kernel_regularizer=None,
            recurrent_regularizer=None,
            bias_regularizer=None,
            activity_regularizer=None,
            kernel_constraint=None,
            recurrent_constraint=None,
            bias_constraint=None,
            dropout=0.5,
            recurrent_dropout=0.2,
            return_sequences=True,
        )
    )(mask)

    drop = tf.keras.layers.Dropout(0.2)(BiLSTM)

    x = tf.keras.layers.MultiHeadAttention(num_heads=6, key_dim=30)(drop, drop)

    # Add&Norm
    x = tf.keras.layers.Add()([x, BiLSTM])
    x = tf.keras.layers.LayerNormalization()(x)

    output = denselayer(x)

    # model = tf.keras.Model(input, output)

    # Compile the model with set paramethers.
    model1 = tf.keras.Model(input, output)
    model1.compile(optimizer=optimizer, loss=loss, metrics=metrics)

    model1.summary()

    # Fit the model
    VAL_SPLIT = 0.1
    BATCH_SIZE = 32
    EPOCHS = 50

    history1 = model1.fit(x=X_train, y=y_train, batch_size=BATCH_SIZE, epochs=EPOCHS,
                          validation_split=VAL_SPLIT)
