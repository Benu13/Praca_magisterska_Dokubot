import tensorflow as tf
import json
import spacy
from typing import Union
import numpy as np
import keras.backend as K
from numpy import dot
from numpy.linalg import norm
from functools import lru_cache


def pad_array(word, length):
    word_padded = np.zeros([1, length]).astype(np.int32)
    if len(word[0]) > length:
        word_padded[0][:] = word[0][0:length]
    else:
        word_padded[0][0:len(word[0])] = word[0]
    return word_padded

def lev_dist(a, b):
    '''
    This function will calculate the levenshtein distance between two input
    strings a and b
    '''

    @lru_cache(None)  # for memorization
    def min_dist(s1, s2):

        if s1 == len(a) or s2 == len(b):
            return len(a) - s1 + len(b) - s2
        # no change required
        if a[s1] == b[s2]:
            return min_dist(s1 + 1, s2 + 1)

        return 1 + min(
            min_dist(s1, s2 + 1),  # insert character
            min_dist(s1 + 1, s2),  # delete character
            min_dist(s1 + 1, s2 + 1),  # replace character
        )
    return min_dist(0, 0)

def check_similarity(token, lookup, type ='cs'):
    if type == 'cs':
        c_simil = -1
        sim_item = None
        for item in lookup:
            cs = dot(token.vector, item['vector'])/(norm(token.vector)*norm(item['vector']))
            if cs > c_simil:
                c_simil = cs
                sim_item = item

        return [sim_item, c_simil]

    elif type == 'ed':
        d_simil = 100
        sim_item = None
        for item in lookup:
            ed = np.linalg.norm(token.vector,item['vector'])
            if ed < d_simil:
                d_simil = ed
                sim_item = item

            return [sim_item, d_simil]

    elif type == 'lev':
        sim_item = None
        lev_d = 10
        for item in lookup:
            ld = lev_dist(token.word, item['word'])
            if ld < lev_d:
                sim_item = item
                lev_d = ld
            if lev_d == 1:
                break
        return [sim_item, lev_d]


class wToken():
    def __init__(self, word, is_oov, lemma, vector):
        self.word = word
        self.chars = list(word)
        self.chars_tokens = None
        self.is_oov = is_oov
        self.lemma = lemma
        self.vector = vector
        self.slot = None
        self.corrected_word = None
        self.corr_word_cs = None
        self.form = None
        self.origin = None
        self.is_logic = False
        self.logic = None


class DocToken():
    def __init__(self, doc_wtokens):
        self.tokens = doc_wtokens
        self.word = ' '.join([word.word for word in doc_wtokens])
        self.lemma = ' '.join([word.lemma for word in doc_wtokens])
        self.origin = self.get_origin()

    def get_origin(self):
        origin = []
        for word in self.tokens:
            if word.origin == "unknown":
                origin.append(word.lemma)
            else:
                origin.append(word.origin)
        return ' '.join(origin)


class KeyToken():
    def __init__(self, key_wtokens):
        self.tokens = key_wtokens
        self.word = ' '.join([word.word for word in key_wtokens])
        self.lemma = ' '.join([word.lemma for word in key_wtokens])


class LogicToken():
    @classmethod
    def artifical(cls, logic):
        return cls(artifical_logic = logic)

    def __init__(self, logic_wtokens=[], artifical_logic=None):
        self.tokens = logic_wtokens
        self.word = ' '.join([word.word for word in logic_wtokens])
        if not artifical_logic:
            self.logic = self.get_logic(logic_wtokens)
            self.logic_pl = self.get_logic_pl()
            self.unidentified = False
            self.conflicting = False
        else:
            self.logic = artifical_logic

    def get_logic_pl(self):
        if self.logic == 'OR':
            logic_pl = 'lub'
        elif self.logic == 'AND':
            logic_pl = 'oraz'
        elif self.logic == 'AND NOT':
            logic_pl = 'oraz nie'
        elif self.logic == 'OR NOT':
            logic_pl = 'lub nie'
        else:
            logic_pl = 'nieznany'

        return logic_pl

    def get_logic(self, wtokens):
        if len(wtokens) > 1:
            comb_logic = [w.logic for w in wtokens if w.logic not in ["AMB", 'NEU']] #TODO change to neutral
            if len(set(comb_logic)) > 1:
                if all(l in comb_logic for l in ['NEG', 'AND']):
                    return 'AND NOT'
                elif all(l in comb_logic for l in ['NEG', 'OR']):
                    return 'OR NOT'
                else:
                    self.conflicting = True
                    return 'UNI'
            else:
                return comb_logic[0]
        else:
            return wtokens[0].logic


class Sentence():
    def __init__(self, sentence, doc):
        self.sentence = sentence
        self.sentence_slots = []
        self.sentence_slots_id = []
        self.Tokens = []
        self.essence = []
        self.essence_operators = []
        for token in doc:
            self.Tokens.append(wToken(token.text, token.is_oov, token.lemma_, token.vector))

    def __iter__(self):
        for token in self.Tokens:
            yield token

    def __len__(self):
        return len(self.Tokens)

    def __getitem__(self, ind):
        return self.Tokens[ind]

    def extract_data_ff(self, lookup_docs=None, lookup_choice=None, type='lev'):
        search_for = {'doc_types': None, 'form': None, 'keywords': None, 'key_operators': None, 'doc_operators': None}
        doc_types = []
        doc_type = []
        keywords = []
        keyword = []
        key_operators = []
        doc_operators = []
        operator = []

        for token in self.Tokens:
            if token.slot in ["B-Doc_type", "I-Doc_type", "Doc_type"]:
                if keyword:
                    keywords.append(KeyToken(keyword))
                if keywords:
                    if operator:
                        key_operators.append(LogicToken(operator))
                        operator = []

                    if key_operators:
                        if len(key_operators) != len(keywords):
                            self.essence_operators.append("AMB")
                        else:
                            self.essence_operators.append(key_operators.pop())

                        search_for['key_operators'] = key_operators
                        key_operators = []
                    if doc_operators:
                        search_for['doc_operators'] = doc_operators
                        doc_operators = []
                    search_for['keywords'] = keywords
                    keywords = []

                    if not doc_types:
                        self.essence.append(search_for)
                        search_for = {'doc_types': None, 'form': None, 'keywords': None, 'key_operators': None, 'doc_operators': None}

                else:
                    if operator:
                        doc_operators.append(LogicToken(operator))
                        operator = []

                item = [d for d in lookup_docs if d['word'] == token.word]
                if not item:
                    corrected_form, token.corr_word_cs = check_similarity(token, lookup_docs, type=type)
                    token.corrected_word = corrected_form['word']
                    token.form = corrected_form['form']
                    token.origin = corrected_form['original']
                    if token.corr_word_cs > 4:
                        token.corrected_word = "unknown"
                        token.form = 'hom'
                        token.origin = "unknown"
                    doc_type.append(token)
                else:
                    token.corrected_word = item[0]['word']
                    token.form = item[0]['form']
                    token.origin = item[0]['original']
                    doc_type.append(token)

                if search_for['form'] != 'pl' and token.form != 'hom':
                    search_for['form'] = token.form
                elif not search_for['form'] and token.form == 'hom':
                    search_for['form'] = token.form

            elif token.slot in ["B-keyword","I-keyword"]:
                if doc_type:
                    doc_types.append(DocToken(doc_type))
                    doc_type = []
                if doc_types:
                    if operator:
                        doc_operators.append(LogicToken(operator))
                        operator = []
                    search_for['doc_types'] = doc_types
                    doc_types = []
                if operator:
                    key_operators.append(LogicToken(operator))
                    operator = []
                keyword.append(token)

            elif token.slot in ['B-Choice', 'I-Choice']:
                item = [d for d in lookup_choice if d['word'] == token.word]
                if not item:
                    corrected_form, token.corr_word_cs = check_similarity(token, lookup_choice, type=type)
                    co = corrected_form['logic']
                else:
                    co = item[0]['logic']
                token.logic = co
                operator.append(token)

                if doc_type:
                    doc_types.append(DocToken(doc_type))
                    doc_type = []
                if keyword:
                    keywords.append(KeyToken(keyword))
                    keyword = []

            elif token.slot in ['O']:
                if token.word == ',':
                    if doc_type:
                        token.logic = 'NEU'
                        operator.append(token)
                        doc_types.append(DocToken(doc_type))
                        doc_type = []
                    if keyword:
                        token.logic = 'NEU'
                        operator.append(token)
                        keywords.append(KeyToken(keyword))
                        keyword = []

        if doc_type:
            doc_types.append(DocToken(doc_type))
        if doc_types:
            search_for['doc_types'] = doc_types
        if doc_operators:
            search_for['doc_operators'] = doc_operators

        if keyword:
            keywords.append(KeyToken(keyword))
        if keywords:
            search_for['keywords'] = keywords
        if key_operators:
            key_operators = key_operators
            search_for['key_operators'] = key_operators

        if search_for['keywords'] or search_for['doc_types']:
            self.essence.append(search_for)

    def correct_misspell(self, lookup, type):
        for token in self.Tokens:
            if token.slot == "doc_type" and not any(d['word'] == token.word for d in lookup):
                token.corrected_word, token.corr_word_cs, token.form = check_similarity(token, lookup, type=type)
                return token.corrected_word, token.form

    def disambiguate_operators(self, operators, alg='backprop', last_operator ="AND"):
        if alg == 'FFa':
            # assume comma as and with forward flow
            for i in range(len(operators)):
                if operators[i] == 'NEU':
                    operators[i] = 'AND'
            return operators
        elif alg == 'backprop':
            # logic operator backpropagation
            last_op = last_operator
            for i in reversed(range(len(operators))):
                if operators[i] == 'NEU':
                    operators[i] = last_op
                else:
                    last_op = operators[i]
            return operators

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


class VecMean:
    def __int__(self, embedding_dimention):
        self.name = 'Mean OOV vector initializer'
        self.embedding_dimention = embedding_dimention

    def __call__(self, doc):
        word_vectors = np.zeros([1, self.embedding_dimention])
        i = 1
        for token in doc:
            if not token.is_oov:
                word_vectors += token.vector.tolist()
            else:
                token.vector = np.array(word_vectors/i).astype(np.float32)
                word_vectors += token.vector.tolist()
            i = i + 1
        return doc


class VecRand:
    def __int__(self, embedding_dimention):
        self.name = 'Rand OOV vector initializer'
        self.embedding_dimention = embedding_dimention

    def __call__(self, doc):
        i = 1
        for token in doc:
            if token.is_oov:
                token.vector = np.random.rand(1,self.embedding_dimention).astype(np.float32)
        return doc


class SlotFiller(object):

    @classmethod
    def load(cls, slot_model_path, slot_lookup_path):
        slot_filler = tf.keras.models.load_model(slot_model_path)
        if slot_lookup_path:
            with open(slot_lookup_path, 'r',encoding='utf-8-sig') as f:
                lookup = json.load(f)

            return cls(slot_filler, lookup=lookup)
        else:
            return cls(slot_filler)

    def __init__(self, slot_filler, lookup=None):
        self._slot_filler = slot_filler
        self._lookup = lookup
        #load size of input (to pad and max sent len)
        self.max_sentence_length = self._slot_filler.layers[0].output_shape[0][1]
        self.embedding_dimention = self._slot_filler.layers[0].output_shape[0][2]

    def __call__(self, doc):
        word_vectors = np.zeros([self.max_sentence_length, self.embedding_dimention])
        i = 0
        for token in doc:
            if i == self.max_sentence_length:
                break
            token_vector = token.vector
            word_vectors[i][:] = token.vector
            i+=1

        sentence_slots = self._slot_filler.predict(np.expand_dims(word_vectors,0), verbose=0)
        doc.sentence_slots_id = np.argmax(sentence_slots[0], axis=1)[0:len(doc)]
        if self._lookup:
            for i in range(len(doc)):
                doc[i].slot = self._lookup[str(doc.sentence_slots_id[i])]
            doc.sentence_slots = [self._lookup[str(key)] for key in doc.sentence_slots_id]

        return doc

class Dokubot():

    def __init__(self, config):
        self.model_name = "Dokubot"
        self.spacy_size = config['spacy_size']

        try:
            self.slot_lookup_path = config['paths']['slot_lookup_path']
        except KeyError:
            self.slot_lookup_path = None

        self.correct_misspells = config['correct_misspell']
        if self.correct_misspells:
            with open(config['paths']['misspell_lookup_path'], 'r', encoding='utf-8-sig') as f:
                self.misspells_lookup = json.load(f)

        with open(config['paths']['choice_lookup_path'], 'r', encoding='utf-8-sig') as f:
            self.choice_lookup = json.load(f)

        self.misspells_correct_algorithm = config['misspell_cor_algorithm']
        if self.slot_lookup_path:
            self.slotF = SlotFiller.load(config['paths']['slot_filler_path'], self.slot_lookup_path)
        else:
            self.slotF = SlotFiller.load(config['paths']['slot_filler_path'])

        self.max_sentence_length = 30
        if config['spacy_from_path']:
            self.nlp = spacy.load(config['paths']['spacy_path'], exclude=config['spacy_disable'])
        else:
            if self.spacy_size == 'lg':
                self.nlp = spacy.load('pl_core_news_lg', disable=config.disable)
            elif self.spacy_size == 'md':
                self.nlp = spacy.load('pl_core_news_md', disable=config.disable)
            elif self.spacy_size == 'sm':
                self.nlp = spacy.load('pl_core_news_md', disable=config.disable)

        self.OOV_handler_type = config['OOV_handler_type']
        if self.OOV_handler_type == 'mimic':
            self.OOV_handler = Mimic.load(config['paths']['mimic_path'], config['paths']['char2tok_path'])
        elif self.OOV_handler_type == 'mean':
            self.OOV_handler = VecMean()
        elif self.OOV_handler_type == 'random':
            self.OOV_handler = VecRand()
        elif self.OOV_handler_type == 'None':
            self.OOV_handler = None
        else:
            raise ValueError('Unknown OOV handler type.')

    def extract(self, sentence):
        sent = Sentence(sentence, self.nlp(sentence))
        if self.OOV_handler:
            self.OOV_handler(sent)
        self.slotF(sent)
        if self.correct_misspells:
            sent.extract_data_ff(lookup_docs=self.misspells_lookup,
                                 lookup_choice=self.choice_lookup,
                                 type=self.misspells_correct_algorithm)
        return sent


def create_lookup(words, nlp):
    lookup = []
    for word in words:
        token = nlp(word)
        lookup.append({'word': word,
                       'vector': token[0].vector.tolist()})

    return lookup
