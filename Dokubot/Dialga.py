### FOR DIALOG MANAGEMENT

'''
-> Write greeting and ask what is person looking for
-> check if greeting back - if greeting back send ':)' and ask what are they looking for again
-> User input text
-> Run through model
-> get sentence class
-> run logic handling:
    -> check if everything is alright (keys = key logic -1, docs = docs logic -1)
    -> if alright assert logic operatos
    -> if ambiguous ask:
        -> if 2 opposite logic operators are in one operator slot (['AND', 'OR']) ast whitch one
        -> if logic ambigous list possibilities (Logic handler)
        -> if unable ask to rephrase it (make it simpler)

-> if only docs - ask for keys
-> if only keys and doc type all - ask for preferred doc type
---
-> form query and search through keywords database
-> if to many results ask if he has another keyword
-> if too little - offer to search through ngrams

-> output positions with maximum value from database matching keywords
'''
from Dokubot.LoadModels import Dokubot, LogicToken, KeyToken, check_similarity, wToken, DocToken
from Dokubot.LogicHandler import LogicHandler
import random
from collections import Counter
import pandas as pd
import re


def text_cleaner(text: str) -> str:
    # Remove: punctuations, URLs, numbers, unnecesary or unknown symbols
    # Do: lower case, connect words split by new line

    # Input:
    # text: string - user specified text to clean
    #
    # Output:
    # Cleaned text

    # TODO - test it on different documents and rewrite it better, test time

    text = text.replace(u'-\n', u'') # connect words split by new line
    text = re.sub(r"\S*https?:\S*", "", text) # remove links
    text = re.sub(r"\S*@?:\S*", "", text)  # remove links

    #text = text.translate(str.maketrans('', '', digits)) # remove digits
    #text = text.translate(str.maketrans('', '','!@#$%^&*()[]{};/<>`~-=_+|')) # remove punctuation
    text = text.replace(r"!?@#$%^&*()[]{};/<>\|`~-=_+.", "")
    text = text.replace(r",", ", ")
    text = text.lower() # lowercase text
    text = ' '.join(text.split()) # remove unnecessary whitespaces

    return text

greetings = ["Cześć, jakiego dokumentu szukasz?", "Hejka, jakiego dokumentu dzisiaj poszukujesz?", "Jaki dokument wariacie?",
             "Elo byq, jaki dokumencik zapodać?", "Miło cię widzieć, jakiego dokumentu szukasz?"]
retry_responses = ["Spróbujmy jeszcze raz...", "It's rewind time!", "Od nowa!", "Jeszcze jeden raz!",
                   "Odwracam biegunowość!"]
ask_for_doc = ["To co podać?", "No to jaki dokumencik?", "No to czego szukamy tym razem?", "Pokazać ci moje towary?",
               "To o czym myślisz?", "Masz pomysł co chciałbyś przeczytać?"]
greet_reactions = [":)", ":-)", ":>", "OwO", "( ͡ʘ ͜ʖ ͡ʘ)", "(͠≖ ͜ʖ͠≖)", "( ͡ᵔ ͜ʖ ͡ᵔ )"]
UNI_found = ['Nie rozumiem, to w końcu jak ma być: ', "A z tym to jak: ", "Coś jest nie tak, miało być: ", "Bo tutaj jest błąd, chodzi Ci o: "]
SCL_found = ['Powoli, bo nie rozumiem, o którą wersję Ci chodzi?', "Już już, tylko jak to rozczytać?", "O co dokładnie tutaj chodzi?"]
wrong_choice = ["Tylko że taki wybór nie istnieje...", "XD", "No już już, nie ma testowania", "Bo jeszcze znajdziesz błąd",
                "Opanuj się", "Nie pędź tak proszę, daj odpocząć", "Żart...ale jak to?", "Zagłada przybędzie z kanalizacji",
                "Jak to jest być botem, dobrze czy nie dobrze?"]
no_tags = ['Można wiedzieć o czym?', 'Co dokładnie ma zawierać?', 'O czym szukasz tych dokumentów?',
           'A te dokumenty to o czym dokładnie mają być?']
prep_ready = ['Oki doki', 'Już szukamy', 'No to działamy', 'Chyba rozumiem', 'Na tropie']
ask_pref_doc = ['Jakieś konkretne typy dokumentów?', 'Masz może preferencje co do typu dokumentu?', 'Jakiś typ dokumentu czy obojętenie?']
ask_for_keys = ['Hmm, a o czym dokładnie szukasz tych dokumnetów?', 'Można zapytać o czym?', 'Już się tym zajmuję, tylko powiedz jeszcze o czym?',
                'Jaki temat tych dokumentów', 'Jakie tagi Cię interesują?', 'Można prosić coś więcej o temacie?']
dead_end = ['Nie to nie', 'No trudno, bywaj', 'Alright then keep your secrets', 'W porządku', '¯\_(ツ)_/¯', '( ͠° ͟ʖ ͡°)', 'No troszkę niezręczna sytuacja nie powiem (⊙︿⊙ ✿)']
negation = ['nie', 'nope', 'obojętnie', 'nie mam', 'nie wiem', 'nie chcę', 'nie potrzebuję', 'dowolnie', 'zgadnij',
            'domyśl się', 'nie podam', 'nie powiem', 'nie powiem ci', 'dowolnie', 'nie interesuje mnie to',
            'bynajmniej', 'nigdy', 'w żdanym razie', 'nie ma mowy', 'jeszcze czego', 'nic z tego', 'nie ma o czym mówić',
            'broń boże', 'absolutnie', 'absolutnie nie', 'nic z tego', 'pod żadnym pozorem']

greet = ['cześć', 'siemka', 'elo elo', 'witam', 'no witam', 'gitara siema', 'czołem', 'siemandero', 'elo', 'hej',"hejo",
         'czółko', 'strzałka', 'elo byku', 'elo byq',' dzień dobry', 'dobry', 'witam witam', 'dobry wieczór', "no elo"]

select_all = ['wszystkie', 'pokaż wszystkie', 'podeślij wszystkie', 'daj wszystkie', 'mogą być wszystkie', 'pokaż całość',
              'całość', 'każdy', 'pokaż co masz', 'daj wszystko', 'podeślij wszystko', 'pokaż wszystko']
select_best = ['daj nalepszy', 'podeślij najlepszy', 'najbardziej pasujący', 'najlepszy', 'tylko najlepszy', 'pokaż mi tylko najlepszy',
               'daj mi tylko najlepszy', 'podeślij mi najbardziej pasujący', 'podeślij mi najlepszy', 'daj mi najlepszy',
               'daj mi najbardziej pasujący']
ask_tag = ['To jaki tag dodajemy?', 'To co dadać?', 'Jaki tag wariacie?', 'To o jakim tagu myślisz?', 'Napisz mi tag do dodania']

class Dialog(Dokubot):

    def __init__(self, config):
        super().__init__(config)
        self.end_session = False
        self.doc_form = None
        self.Doc_hom_flag = True
        self.LH = LogicHandler()
        self.essence = []
        self.essence_operators = []

        self.doc_established = False
        self.doc_query = None
        self.doc_all_flag = False
        self.doc_pref = []
        self.doc_logic = ['None']
        self.doc_logic_all = []

        self.key_logic = ['None']
        self.key_established = False
        self.key_query = None
        self.key_logic_all = []

    def reset(self):
        self.end_session = False
        self.doc_form = None
        self.Doc_hom_flag = True
        self.LH = LogicHandler()
        self.essence = []

        self.doc_established = False
        self.doc_query = None
        self.doc_all_flag = False
        self.doc_pref = []
        self.doc_logic = ['None']
        self.doc_logic_all = []

        self.key_logic = ['None']
        self.key_established = False
        self.key_query = None
        self.key_logic_all = []

    def soft_reset(self):
        self.doc_form = None
        self.doc_established = False
        self.doc_query = None
        self.doc_all_flag = False
        self.doc_pref = []
        self.doc_logic = ['None']
        self.key_logic = ['None']
        self.key_established = False
        self.key_query = None


    def doc_all_pref(self, docs):
        if docs:
            for i in range(len(docs)):
                if docs[i].origin in ['coś', 'czegoś', 'dokument', 'papier', 'cokolwiek', 'pozycja']:
                    if not self.doc_all_flag:
                        self.doc_all_flag = True
                    else:
                        pass
                else:
                    self.doc_pref.append(docs[i].origin)

    def isnegation(self, text):
        if text.lower() in negation:
            return True
        else:
            return False

    def isgreet(self, text):
        if text.lower() in greet or len(text.split(' ')) < 2:
            return True
        else:
            return False

    def preprocess_utterance(self, utterance):
        return utterance.lower()

    def long_key_recombobulator(self, key:KeyToken):
        przyim = ["na", "o", "w", "z","za","ku", "do", "bez", "pod", "przed", "nad", "dla", "między", "przez", "po"]
        j=0
        keys = []
        key_w = []
        for i in key.lemma.split():
            if i in przyim and key_w:
                keys.append(key_w)
                key_w = []
            elif i in przyim:
                j += 1
                continue
            else:
                key_w.append(key.tokens[j])
            j += 1
        if key_w:
            keys.append(key_w)

        #key_len = len(key.tokens)
        #ng = ngrams(key.lemma.split(), 2)
        #a = list(ng)
        #if key_len > 1:
        #    full_s.append("(")
       #     for i in range(len(key.tokens)-1):
        #        full_s.append(KeyToken([key.tokens[i]]))
       #         full_s.append(LogicToken.artifical(logic="OR"))
        #    full_s.append(KeyToken([key.tokens[-1]]))
        #full_s.append(")")
        fs = []
        for key in keys:
            key_len = len(key)
            if key_len > 2:
                full_s = ["("]
                #full_s.append(LogicToken.artifical(logic="OR"))
                full_s.append("(")
                for i in range(len(key)-2):
                    full_s.append(KeyToken([key[i],key[i+1]]))
                    full_s.append(LogicToken.artifical(logic="OR"))
                full_s.append(KeyToken([key[-2], key[-1]]))
                full_s.append(")")
                full_s.extend([LogicToken.artifical(logic="OR"), KeyToken(key), ")"])
                fs.append(full_s)
            else:
                fs.append(KeyToken(key))

        if len(fs) > 1:
            out = ["("]
            for i in range(len(fs)-1):
                out.append(fs[i])
                out.append(LogicToken.artifical(logic="OR"))
            out.append(fs[-1])
            out.append(")")
        else:
            out = fs[0]

        return out

    def filter_in_data(self, df, key):
        mask = df.keywords.apply(lambda x: key in x)
        df2 = df[mask]
        for index, row in df2.iterrows():
            df2['score'][index] += row['keywords_scores'][row['keywords'].index(key)]
        return df2

    def filter_not_in_data(self, df, key):
        mask = df.keywords.apply(lambda x: key not in x)
        df2 = df[mask]
        return df2

    def check_simil(self, word):
        tt =wToken(word)
        corrected_form, corr_word_cs = check_similarity(tt, self.misspells_lookup, type='lev')
        if corr_word_cs < 3:
            tt.corrected_word = corrected_form['word']
            tt.form = corrected_form['form']
            tt.origin = corrected_form['original']
            tt.word = corrected_form['original']
            tt.lemma = corrected_form['original']
            return DocToken([tt])
        else:
            return None

    def keys_to_query(self):
        sql_query = """SELECT "Document".* FROM "Document"  WHERE """
        sql_query_key = """(EXISTS (SELECT 1 FROM "Keyword" WHERE "Document".id = "Keyword".document_id AND "Keyword"."key" = '%s'))"""

        prepr_q = []
        for keyw in self.key_logic[1]:
            if isinstance(keyw, KeyToken):
                if len(keyw.tokens) > 2:
                    prepr_q.extend(self.long_key_recombobulator(keyw))
                else:
                    prepr_q.append(keyw)
            else:
                prepr_q.append(keyw)

        all_keys = []
        for key in prepr_q:
            if key in ["(",")"]:
                sql_query += key
            elif isinstance(key, LogicToken):
                sql_query += ' ' + key.logic + ' '
            elif isinstance(key, KeyToken):
                all_keys.append(key.lemma)
                key_subs = sql_query_key % key.lemma
                sql_query += key_subs

        return sql_query, all_keys

    def prep_query_data(self, query, keywords):
        all_keys = []
        docs = []
        doc = {'id': None, 'title': None, 'type': None, 'score': None, 'keywords': [], 'keywords_scores': []}
        count = 0

        for user_obj in query:
            doc['id'] = user_obj.id
            doc['title'] = user_obj.title
            doc['type'] = user_obj.doc_type
            count += 1
            score = 0
            for kk in user_obj.keywords:
                if kk.key in keywords:
                    score += kk.value
                else:
                    all_keys.append(kk.key)

                doc['keywords'].append(kk.key)
                doc['keywords_scores'].append(kk.value)

            doc['score'] = score
            docs.append(doc)
            doc = {'id': None, 'title': None, 'type': None, 'score': None, 'keywords': [], 'keywords_scores': []}

        return pd.DataFrame(docs), count, Counter(all_keys).most_common()


    def service(self, logic, essence, op_type):  # UNI_D, NO_D, SCL_D, CL_D
        if op_type == 'docs':
            keys = 'doc_types'
            operators = 'doc_operators'
        if op_type == 'keys':
            keys = 'keywords'
            operators = 'key_operators'

        if logic[0] == 'UNI':
            # serve uni token/s
            for i in logic[1]:
                question = random.choice(UNI_found)
                choice = []
                num = 1
                for l in essence[operators][i].tokens:
                    if l.logic != 'AMB':
                        choice.append((num, l.logic, ' '.join(
                            [essence[keys][i].word, l.word, essence[keys][i + 1].word])))
                        num += 1

                print(question)
                for j in choice:
                    print(str(j[0]) + ". " + j[2])

                stop_flag = False
                while not stop_flag:
                    user_choice = input(">> ")
                    try:
                        uc_int = int(user_choice)
                        if uc_int not in range(1, num):
                            print(random.choice(wrong_choice))
                        else:
                            stop_flag = True
                            essence[operators][i].logic = choice[uc_int - 1][1]
                            if choice[uc_int - 1][1] == 'OR':
                                essence[operators][i].logic_pl = 'lub'
                            if choice[uc_int - 1][1] == 'AND':
                                essence[operators][i].logic_pl = 'i'
                    except:
                        print("Opanuj się, tutaj masz tylko wybrać numerek")

            return logic, essence

        if logic[0] == 'NO':
            return ('CL'), essence

        if logic[0] == 'SCL':  # raise select correct logic flag
            question = random.choice(SCL_found)
            a = logic[1][0][0]
            for i in range(len(logic[1])):
                print(str(i + 1) + '. ' + logic[1][i][0])

            # wybór wersji
            stop_flag = False
            while not stop_flag:
                user_choice = input(">> ")
                try:
                    uc_int = int(user_choice)
                    if uc_int not in range(1, len(logic[1]) + 1):
                        print(random.choice(wrong_choice))
                    else:
                        stop_flag = True
                        logic = ('CL', logic[1][uc_int - 1][1])
                except:
                    print("Opanuj się, tutaj masz tylko wybrać numerek")

            if op_type == 'docs':
                self.doc_established = True
            if op_type == 'keys':
                self.key_established = True

            return logic, essence

        if logic[0] == 'CL':
            if op_type == 'docs':
                self.doc_established = True
            if op_type == 'keys':
                self.key_established = True

            return logic, essence
